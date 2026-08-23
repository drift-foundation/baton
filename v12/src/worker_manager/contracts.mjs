// The frozen `urn:baton:worker-control:1.0` boundary, in product code.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
// (W2929), against the contract frozen by W1439 and amended three times by
// W4487.
//
// WHAT THIS MODULE IS FOR. Everything below the manager's orchestration
// that decides whether a document may be TRUSTED: exact version and
// capability negotiation, canonical bytes, digests, the operation
// signature, the claim-token verifier, and the semantic rules §12 says a
// schema cannot express. Nothing here reaches a database, an adapter or a
// provider.
//
// WHY THE SCHEMA IS A SEALED COPY. `schema/worker-control-1.0.schema.json`
// is a byte copy of the frozen design asset, and a regression asserts it
// stays byte-identical. A product that paraphrased the schema would be a
// second, quieter contract: the first time the two disagreed, the design
// record would say one thing and the running manager another, and only
// the running one would matter.

import { createHash, timingSafeEqual } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

export class ContractError extends Error {
	constructor(category, code, message) {
		super(message);
		this.name = "ContractError";
		// The CLOSED error pair, carried on the error itself. A caller
		// mapping a refusal onto the wire never has to re-derive which
		// category a message belongs to, which is how the two drift.
		this.category = category;
		this.code = code;
	}
}

const HERE = dirname(fileURLToPath(import.meta.url));
export const SCHEMA_PATH = join(HERE, "schema", "worker-control-1.0.schema.json");
export const SCHEMA_BYTES = readFileSync(SCHEMA_PATH);
export const SCHEMA = JSON.parse(SCHEMA_BYTES.toString("utf8"));

export const PROTOCOL = "baton.worker-control";
export const VERSION = Object.freeze({ major: 1, minor: 0 });

// §2's closed capability set. `core.errors` is mandatory for every 1.0
// connection; the rest gate exact kinds.
export const CAPABILITIES = Object.freeze([
	"core.errors", "core.offer", "core.assignment", "core.runtime-lifecycle",
	"core.activity", "core.output-freeze", "core.proposal", "core.receipts",
]);

// §9's closed category/code PAIRING.
//
// The frozen schema carries the two vocabularies as flat enums and does not
// pair them — which is precisely why §12 makes the pairing a semantic rule.
// So it is written out here, and a regression asserts that the union of
// these pairs is EXACTLY the schema's `category` and `code` enums. A code
// added to the frozen schema without a category then fails loudly instead
// of quietly becoming unmappable.
export const ERROR_CODES = Object.freeze({
	refused: Object.freeze(["precondition", "unsupported-version", "capability",
	                        "extension", "operation-collision", "already-terminal"]),
	ambiguous: Object.freeze(["operation", "runtime-start", "collection"]),
	unavailable: Object.freeze(["transport", "authority", "artifact-store",
	                            "source-provider"]),
	policy: Object.freeze(["denied", "profile-uncertified", "credential-lifetime",
	                       "retention"]),
	integrity: Object.freeze(["schema", "digest", "path", "file-type", "limit",
	                          "secret-leak"]),
	"stale-assignment": Object.freeze(["ended", "generation", "contract", "target"]),
	"runtime-observation": Object.freeze(["identity-mismatch", "duplicate-runtime",
	                                      "quiescence-unknown", "state-regression"]),
});

// What the FROZEN SCHEMA admits, for the agreement regression above.
export const SCHEMA_ERROR_CATEGORIES =
	Object.freeze([...SCHEMA.$defs.controlErrorBody.properties.category.enum]);
export const SCHEMA_ERROR_CODES =
	Object.freeze([...SCHEMA.$defs.controlErrorBody.properties.code.enum]);

// ---------------------------------------------------------------------------
// §3.2 canonical bytes and digests
// ---------------------------------------------------------------------------

// RFC 8785 canonicalization, CLOSED over the value space this contract
// admits: objects, arrays, strings, booleans, null and JSON-safe
// NON-NEGATIVE integers.
//
// Review 2026-08-22 [P1]: this checked `Number.isSafeInteger` and stopped
// there, so `-1` serialized as `-1`, negative zero serialized as `0`, and a
// lone UTF-16 surrogate escaped happily — all three acquiring body and
// operation digests under a function presented as the frozen canonical
// trust boundary. §3.2 forbids the first two outright and RFC 8785 requires
// invalid Unicode to FAIL rather than be repaired.
//
// WHY THIS STAYS A LOCAL IMPLEMENTATION while the SCHEMA validator does
// not. RFC 8785's genuinely hard part is number formatting, and this
// contract has no numbers to format: §3.2 forbids floating point, NaN,
// infinity and negative zero in durable documents, so the admitted space is
// non-negative safe integers, which have exactly one spelling. What remains
// is member ordering by UTF-16 code unit — which `Array.prototype.sort` on
// JavaScript strings already is — and string escaping, which
// `JSON.stringify` already does per RFC 8785 once lone surrogates are
// refused. The refusals below are what close it; a JSON Schema validator,
// by contrast, has a large construct surface I would be re-deriving, which
// is exactly the mistake this repository has caught me making before.
export function canonicalBytes(value) {
	return Buffer.from(canonicalString(value), "utf8");
}

const LONE_SURROGATE = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/;

function canonicalString(value) {
	if (value === null) return "null";
	if (typeof value === "boolean") return value ? "true" : "false";
	if (typeof value === "number") {
		// `Object.is` because `-0 === 0`: the comparison that reads
		// naturally is exactly the one that cannot see negative zero.
		if (Object.is(value, -0)) {
			throw new ContractError("integrity", "schema",
				"§3.2 forbids negative zero in a durable document; it is "
				+ "refused rather than serialized as 0");
		}
		if (!Number.isSafeInteger(value) || value < 0) {
			throw new ContractError("integrity", "schema",
				`canonical JSON here admits only JSON-safe NON-NEGATIVE `
				+ `integers; ${value} is not one (§3.2 forbids floating `
				+ `point, NaN, infinity, negative zero and, in this schema's `
				+ `value space, negative integers)`);
		}
		return String(value);
	}
	if (typeof value === "string") {
		if (LONE_SURROGATE.test(value)) {
			throw new ContractError("integrity", "schema",
				"the string carries a lone UTF-16 surrogate; RFC 8785 "
				+ "requires invalid Unicode to fail rather than be repaired "
				+ "into a digestible document");
		}
		return JSON.stringify(value);
	}
	if (Array.isArray(value)) {
		// A SPARSE array is not a JSON array: its holes would serialize as
		// `null` and silently change the document being digested.
		for (let at = 0; at < value.length; at += 1) {
			if (!Object.hasOwn(value, at)) {
				throw new ContractError("integrity", "schema",
					`the array has a hole at index ${at}; a sparse array is `
					+ `not a JSON array and must not acquire a digest`);
			}
		}
		return `[${value.map(canonicalString).join(",")}]`;
	}
	if (typeof value === "object") {
		// A PLAIN object only. A Date, a Map, a class instance or a
		// null-prototype bag would each serialize as something other than
		// what the caller meant, and a digest over "something else" is the
		// one failure this boundary exists to prevent.
		const prototype = Object.getPrototypeOf(value);
		if (prototype !== Object.prototype && prototype !== null) {
			throw new ContractError("integrity", "schema",
				`canonical JSON admits plain objects only; `
				+ `${value.constructor?.name ?? "this value"} is not one`);
		}
		// RFC 8785 orders members by their UTF-16 code units, which is what
		// `Array.prototype.sort` on JavaScript strings already does.
		// Re-review 2026-08-22 [P1]: the surrogate check ran on string
		// VALUES only, so moving the same malformed Unicode into a member
		// NAME made it digestible. RFC 8785's invalid-Unicode failure is not
		// side-dependent.
		const keys = Object.keys(value).sort();
		for (const key of keys) {
			if (LONE_SURROGATE.test(key)) {
				throw new ContractError("integrity", "schema",
					"a member name carries a lone UTF-16 surrogate; RFC 8785 "
					+ "requires invalid Unicode to fail wherever it sits");
			}
		}
		return `{${keys.map((key) =>
			`${JSON.stringify(key)}:${canonicalString(value[key])}`).join(",")}}`;
	}
	throw new ContractError("integrity", "schema",
		`canonical JSON has no representation for ${typeof value}`);
}

export function digest(value) {
	return "sha256:" + createHash("sha256").update(canonicalBytes(value)).digest("hex");
}

export function digestOfBytes(bytes) {
	return "sha256:" + createHash("sha256").update(bytes).digest("hex");
}

// ---------------------------------------------------------------------------
// The claim-token verifier (W151 §7, pinned by the W4487 re-review)
// ---------------------------------------------------------------------------

// ONE derivation, and this module does not get to choose it. W151 owns the
// offer record, so W151 owns what the verifier IS:
//
//   verifier = "sha256:" + lowercase hex of SHA-256 over the bearer's own
//              UTF-8 bytes
//
// The token's OWN BYTES, not a JSON encoding of them: hashing the encoding
// brings quotes and escaping rules into the value, so two peers that escape
// a character differently derive different verifiers for the same secret.
// That is exactly the defect the re-review of 2026-08-22T14:57:26Z found
// between the two design models, and W2929's plan item 1b says in as many
// words not to derive a second value here.
//
// The golden pair below is the one pinned in both models, as a LITERAL. A
// recomputation would agree with any derivation, including a wrong one.
export function tokenVerifier(token) {
	if (typeof token !== "string" || token.length === 0) {
		throw new ContractError("integrity", "schema",
			"a claim bearer is a non-empty string");
	}
	return "sha256:" + createHash("sha256").update(token, "utf8").digest("hex");
}

export const GOLDEN_BEARER = "x".repeat(43);
export const GOLDEN_VERIFIER =
	"sha256:cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be15268523776ac26a1";

// ---------------------------------------------------------------------------
// §4.2 the operation signature
// ---------------------------------------------------------------------------

// The payload is EXACT, and this module recomputes it rather than trusting
// the one it was sent. The review of 2026-08-22T14:39:32Z is why: a decline
// could change its durable reason, recompute only `body_digest`, keep the
// old signature, and be journalled as an exact replay of the first decline.
// A binding nothing recomputes is a field.
//
// The KIND is inside the identity, so the signature is never the body
// digest: `output.freeze` and `output.collect` carry the same body, and one
// operation id reused across the two must collide rather than replay.
//
// A bearer operand rides as its VERIFIER, never literally: a signature is
// durable, §13 keeps the bearer off durable surfaces, and dropping it would
// make an accept under a reused id with a different token an exact replay.
const BEARER_FIELDS = Object.freeze(["claim_token"]);

export function operationSignaturePayload(kind, body) {
	const operands = structuredClone(body);
	for (const field of BEARER_FIELDS) {
		if (Object.hasOwn(operands, field)) {
			const bearer = operands[field];
			delete operands[field];
			operands[`${field}_verifier`] =
				bearer === null ? null : tokenVerifier(bearer);
		}
	}
	return { kind, operands };
}

export function operationSignature(kind, body) {
	return digest(operationSignaturePayload(kind, body));
}

// ---------------------------------------------------------------------------
// §5 the control envelope
// ---------------------------------------------------------------------------

// THE FROZEN SCHEMA, COMPILED, and it runs BEFORE any semantic helper.
//
// Review 2026-08-22 [P1]: nothing here ran the schema. The signature helper
// exempted every `message_type` other than the exact string `command`, so a
// mutating `offer.decide` with a stale signature and `message_type:
// "commmand"` — one letter — took the REPLY exemption and passed. That
// reopens the W4487 integrity hole through a misspelling, and it is the
// smaller half of the problem: required fields, closed enums, limits and
// correlations were all being read by semantic helpers before anything had
// established them.
//
// WHY A LIBRARY AND NOT A LOCAL VALIDATOR. The plan left the choice open.
// JSON Schema's construct surface is large and this repository has caught me
// three times implementing a specification from my reading of it —
// `exec_policy`'s seven rounds are the record. `ajv` is pinned exactly in
// `package.json` and resolved from the committed lockfile, so the prototype
// still fetches nothing at run time and nothing enters the v11 tree.
//
// FORMAT ASSERTIONS ARE OFF DELIBERATELY, and stated rather than defaulted:
// the schema marks locators `format: "uri"`, and §12 rule 4 demands strictly
// MORE than that format does — no credentials, no query, no fragment — which
// `validateUri` enforces below. Turning the weaker check on would suggest the
// stronger one had run.
const _ajv = new Ajv2020({ strict: false, validateFormats: false,
                           allErrors: false });
const _validateDocument = _ajv.compile(SCHEMA);

// Documents THIS module validated, by identity.
//
// Re-review 2026-08-22 [P1]: `verifyOperationSignature` took
// `{ schemaProven: true }` and believed it. Nothing bound that boolean to
// AJV having validated THIS document, so calling the exported helper with a
// misspelled `message_type` and a self-attested flag walked straight back
// into the W4487 reply exemption — the first review's bypass, through a
// lower-level door.
//
// A proof a caller can write is not a proof. The brand is a WeakSet no
// caller can reach, holding only values the validator itself produced, so
// the exemption is unreachable for any document that did not pass the
// frozen schema.
const _validated = new WeakSet();

// The validated value is an INDEPENDENTLY OWNED COPY.
//
// Re-review 2026-08-22 [P1]: this returned its input, so after every check
// passed the caller could mutate the same body's durable operands and the
// value downstream code regarded as validated changed with it — a
// time-of-check/time-of-use alias wearing the word "validated". Every check
// below, and the returned object, now refer to one copy nobody else holds.
export function validateAgainstSchema(document, what = "document") {
	const owned = structuredClone(document);
	if (!_validateDocument(owned)) {
		const first = _validateDocument.errors?.[0];
		throw new ContractError("integrity", "schema",
			`${what} is not a valid baton.worker-control 1.0 document: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	_validated.add(owned);
	return owned;
}

export function verifyBodyDigest(envelope) {
	if (envelope?.body_digest !== digest(envelope?.body)) {
		throw new ContractError("integrity", "digest",
			"body digest does not recompute over canonical body bytes");
	}
}

// §12 rule 9. A REPLY is exempt: §5 says it carries the same operation as
// the request it answers, so its `signature_digest` is the REQUEST's and its
// body is a result rather than the operands. Recomputing over a reply body
// would refuse every conforming reply; the exemption is keyed on
// `message_type` so it cannot become a hole for commands.
function verifyOperationSignature(envelope) {
	const operation = envelope?.operation;
	if (operation === null || operation === undefined) return;
	// Review 2026-08-22 [P1]: the reply exemption is reachable ONLY from a
	// schema-proven document. Before, any `message_type` that was not the
	// exact string `command` took it — so a misspelling turned a mutating
	// command into a reply before anything had proved it was one. The
	// discriminator is trustworthy exactly once the schema has closed its
	// enum, and not one line earlier.
	if (!_validated.has(envelope)) {
		throw new ContractError("integrity", "schema",
			"the operation signature cannot be judged for a document this "
			+ "module did not validate; the frozen schema is what establishes "
			+ "the message type, and the exemption follows from it");
	}
	if (envelope.message_type !== "command") return;
	if (operation.signature_digest !== operationSignature(envelope.kind, envelope.body)) {
		throw new ContractError("integrity", "digest",
			`operation ${operation.operation_id} carries a signature that does `
			+ `not describe its own kind and durable operands; the operation is `
			+ `refused before it is journalled`);
	}
}

// ---------------------------------------------------------------------------
// §2 negotiation
// ---------------------------------------------------------------------------

// EXACT, not "compatible". §2 rejects optimistic minor parsing: a peer that
// accepted 1.1 by ignoring what it did not know would be guessing about
// fields whose absence changes meaning.
//
// Review 2026-08-22 [P1]: this accepted a hello with neither `limits` nor
// `runtime_profile_digest`, COPIED every peer extension into the result
// although no caller had said which it supports, and returned no
// `effective_limits` — so the answer claimed `org.example.not-implemented/1`
// was selected and could not itself validate as a `control.welcome` body.
// "Selected" has to mean an intersection with something.
//
// So negotiation now takes the manager's own policy: which extensions it
// supports, its limits, and its certified runtime profile. It returns the
// COMPLETE frozen welcome body, validated against the schema before it is
// handed back — if this manager cannot form a valid welcome, that is a fault
// here and not something to discover at the peer.
//
// LIMITS INTERSECT AT THE MINIMUM. Each bound says what its side can
// survive; the pair that both survive is the smaller. Taking the manager's
// own numbers would tell a peer to send frames it has just said it cannot
// receive.
export function negotiate(hello, { supported = CAPABILITIES,
                                   extensions: localExtensions = [],
                                   limits, runtimeProfileDigest } = {}) {
	// The hello is SCHEMA-PROVEN first: required members, the closed role
	// and capability enums, `minItems`, `uniqueItems` and the extension
	// pattern are all established before a line below reads them. That is
	// what closes the missing-`limits` half of the review's finding.
	if (limits === undefined || runtimeProfileDigest === undefined) {
		throw new ContractError("refused", "precondition",
			"negotiation needs this manager's own limits and certified "
			+ "runtime profile; a welcome cannot be formed from the peer's "
			+ "hello alone");
	}
	// Re-review 2026-08-22 [P1]: the peer's hello was schema-proven and the
	// LOCAL policy was not, so a manager configured with
	// `runtime_profile_digest: "not-a-digest"` negotiated successfully and
	// that string became trusted state. Being local does not make a
	// malformed identity a certified profile — the frozen constraints apply
	// to whoever supplies the value.
	validateSchemaFragment(limits, "controlLimits", "manager limits");
	validateSchemaFragment(runtimeProfileDigest, "digest",
	                       "manager runtime profile digest");
	// The hello's `extensions` list carries NAMES, and the `$defs.extensions`
	// object is the extension BAG — a different shape. The manager's own
	// supported names are held to the list's own constraint, read off the
	// frozen schema rather than retyped.
	const NAME = SCHEMA.$defs.helloBody.properties.extensions;
	validateSchemaFragment([...localExtensions], NAME,
	                       "manager supported extensions");
	validateSchemaFragment(hello, "helloBody", "control.hello body");
	const offered = hello.supported_versions;
	if (!offered.some((entry) => entry.major === VERSION.major
			&& entry.minor === VERSION.minor)) {
		throw new ContractError("refused", "unsupported-version",
			`this manager speaks exactly ${VERSION.major}.${VERSION.minor}; the `
			+ `peer offered ${JSON.stringify(offered)}`);
	}
	const peer = hello.capabilities;
	const selected = supported.filter((capability) => peer.includes(capability));
	if (!selected.includes("core.errors")) {
		// The schema already requires the peer to offer it; this is the
		// other half — a manager that did not support it could not answer.
		throw new ContractError("refused", "capability",
			"core.errors is mandatory for every 1.0 connection");
	}
	// An extension is negotiated by EXACT name and version or it is not
	// negotiated. The intersection is with what THIS manager implements;
	// echoing the peer's list would claim support this build does not have,
	// and §2 makes sending an unnegotiated extension `refused.extension`.
	const local = new Set(localExtensions);
	const extensions = hello.extensions.filter((entry) => local.has(entry));
	const welcome = {
		selected_version: { ...VERSION },
		capabilities: selected,
		extensions,
		// The pair BOTH sides survive, which is the smaller of the two.
		effective_limits: Object.fromEntries(
			Object.keys(limits).map((key) => [key,
				Math.min(limits[key], hello.limits[key])])),
	};
	// If this manager cannot form a valid welcome, that is a fault HERE.
	// Discovering it at the peer would make our own bug look like theirs.
	validateSchemaFragment(welcome, "welcomeBody", "control.welcome body");
	// The welcome BODY is returned as its own object, exactly the frozen
	// shape. The two profile digests ride beside it rather than inside it:
	// they are what the manager must now compare, and a caller that spread
	// this into a frame would otherwise send fields the schema forbids.
	return { welcome,
	         peer_runtime_profile_digest: hello.runtime_profile_digest,
	         runtime_profile_digest: runtimeProfileDigest };
}

// One `$defs` fragment, compiled once and cached. The frozen schema's
// bodies are reachable by `$ref`, so a fragment check is the same contract
// as the whole-document check rather than a second opinion about it.
const _fragmentValidators = new Map();

export function validateSchemaFragment(value, definition, what) {
	// `definition` is either a `$defs` NAME or an inline subschema drawn
	// from the frozen document. Both compile against the same `$defs`, so
	// neither is a second opinion about the contract.
	if (!_fragmentValidators.has(definition)) {
		_fragmentValidators.set(definition, _ajv.compile(
			typeof definition === "string"
				? { $schema: SCHEMA.$schema, $ref: `#/$defs/${definition}`,
				    $defs: SCHEMA.$defs }
				: { $schema: SCHEMA.$schema, ...definition,
				    $defs: SCHEMA.$defs }));
	}
	const validate = _fragmentValidators.get(definition);
	if (!validate(value)) {
		const first = validate.errors?.[0];
		throw new ContractError("integrity", "schema",
			`${what} is not valid here: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	return value;
}

export function requireNegotiated(negotiated, capability, kind) {
	if (!negotiated.capabilities.includes(capability)) {
		throw new ContractError("refused", "capability",
			`${kind} requires the ${capability} capability, which this `
			+ `connection did not negotiate`);
	}
}

// ---------------------------------------------------------------------------
// §12 semantic validation beyond JSON Schema
// ---------------------------------------------------------------------------

export function validateWorkRef(workRef) {
	if (workRef?.work_id?.split("-", 1)[0] !== workRef?.authority_uuid?.slice(0, 8)) {
		throw new ContractError("integrity", "schema",
			`Work id ${workRef?.work_id} does not carry its authority's prefix`);
	}
}

const SECRET_FIELDS = new Set([
	"claim_token", "password", "authorization", "access_token",
	"refresh_token", "private_key",
]);

// THE EPHEMERAL BEARERS THIS PROCESS KNOWS, BY VALUE.
//
// Round-4 review [P1]: the walk below screened FIELD NAMES only, so a raw
// bearer under `diagnostic`, or interpolated into a durable refusal message,
// was journalled. Both are surfaces §13 names, and a name-only check reads as
// a leak boundary while being a naming convention.
//
// SHAPE CANNOT SUBSTITUTE FOR THIS and the review is right to say so: the
// contract admits any bearer from 32 to 4096 characters, so a rule that
// refused token-shaped strings would refuse ordinary durable operands and
// still miss a short one. The only safe test is against the actual value.
//
// TWO REGISTERS, because two different lifetimes are involved and a `Set`
// conflated them.
//
// `_PINNED` is what this BUILD knows at rest: the golden conformance bearer.
// It is never released, because nothing acquired it and so nothing may hand
// it back — round-5 review [P1] points out that a scoped use of the seed
// could otherwise delete it.
//
// `_live` is a REFERENCE COUNT, not a presence set. Round-5 review [P1]: an
// outer owner holding a bearer and an inner scope using the same value are
// two registrations of one value, and the inner scope's release used to
// delete the outer owner's still-live entry. Presence cannot express shared
// ownership; a count can.
const _PINNED = new Set([GOLDEN_BEARER]);
const _live = new Map();

function* _secrets() {
	yield* _PINNED;
	yield* _live.keys();
}

/** Register an ephemeral secret for as long as it is live.
 *
 *  Registrations NEST. Each one must be matched by exactly one release, and
 *  the value stays live until the last of them. */
export function rememberSecret(value) {
	if (typeof value !== "string" || value.length === 0) {
		throw new ContractError("integrity", "schema",
			"a remembered secret is a non-empty string value");
	}
	_live.set(value, (_live.get(value) ?? 0) + 1);
	return value;
}

/** Release ONE registration. The value stops being live when the last owner
 *  releases it — a verifier is single-use across acceptance, decline and
 *  expiry alike (§12 rule 14), so a spent bearer stops being live, and
 *  keeping dead strings would grow a set every durable write scans.
 *
 *  Returns whether the value is now gone. A pinned value never is: it was
 *  not acquired, so it cannot be handed back. */
export function forgetSecret(value) {
	const held = _live.get(value);
	// NO DYNAMIC OWNER. The call is state-inert — no count to decrement,
	// nothing to delete — but the ANSWER is not about what this call did,
	// it is about whether the value is live now.
	//
	// Round-8 review [P2]: this returned `false` unconditionally, so an
	// unbalanced release of an ordinary value that is already gone reported
	// "still live" while the guard correctly permitted it. That is the same
	// contradiction the pinned case had, pointing the other way, and it
	// survived my own agreement case because that case never released a
	// value twice. Both branches consult the same fact now.
	if (held === undefined) return !_PINNED.has(value);
	if (held > 1) {
		_live.set(value, held - 1);
		return false;
	}
	_live.delete(value);
	// The last DYNAMIC owner released — but "gone" is a statement about
	// whether the value is still live, and a pinned one always is.
	//
	// Round-7 review [P2]: this returned `true` without consulting `_PINNED`,
	// so a caller that had registered the golden bearer and released it was
	// told the value was no longer live while the guard went on refusing it.
	// Not a leak — the guard is the boundary and it was right — but the
	// exported lifecycle answer contradicted the state it enforces, and
	// orchestration reading that answer would draw the wrong conclusion.
	return !_PINNED.has(value);
}

/** Hold a secret for the duration of one act, however that act ends.
 *
 *  Round-5 review [P1]: this released as soon as the act RETURNED, and a
 *  provider act naturally returns a Promise — so the bearer was unregistered
 *  while the work was still pending, which is precisely the call shape the
 *  orchestration slice will use. Returning a pending Promise is not
 *  completion.
 *
 *  A synchronous throw still releases immediately; an asynchronous act keeps
 *  the registration until its Promise settles, either way. */
export function withSecret(value, act) {
	rememberSecret(value);
	let transferred = false;
	try {
		const outcome = act();
		// ONE READ of `then`, and the captured callable is what gets used.
		//
		// Round-6 review [P1]: reading `.then` to CLASSIFY and then handing
		// the value to `Promise.resolve` — which reads it again, and
		// assimilation may read it further — is another
		// time-of-check/time-of-use split. A stateful thenable that offers
		// its continuation on the first read and `undefined` afterwards was
		// classified asynchronous while the continuation was never called:
		// the wrapper settled immediately and released the bearer with the
		// represented act still pending.
		//
		// A read that decides something must be the read that is used. This
		// captures the callable once and assimilates THAT, with its original
		// receiver, so the release cannot happen before the act it belongs
		// to settles.
		const continuation = outcome?.then;
		if (typeof continuation === "function") {
			transferred = true;
			return new Promise((resolve, reject) => {
				continuation.call(outcome, resolve, reject);
			}).finally(() => forgetSecret(value));
		}
		return outcome;
	} finally {
		// A THROWING `then` getter lands here with `transferred` still
		// false, so the synchronous cleanup covers it — a value whose
		// classification failed was never handed to anyone.
		if (!transferred) forgetSecret(value);
	}
}

// §13, and it is a WALK rather than a top-level check because the boundary
// is about what a durable document CONTAINS, at any depth. A bearer nested
// inside a copied decision body is exactly as durable as one at the root.
//
// Both halves are needed and neither implies the other: a field NAMED for a
// secret is refused whatever it holds, because the name says the value is
// one; and a known secret VALUE is refused wherever it appears, because a
// leak does not depend on what the leaking field was called. The value test
// is CONTAINMENT rather than equality — an interpolated refusal message
// carries the bearer just as durably as a bare field does.
export function assertNoDurableSecret(document, where = "document",
                                      secrets = null) {
	const known = secrets ?? _secrets();
	// One materialized list per call, because the walk recurses and a
	// generator is consumed once.
	_walkForSecrets(document, where, [...known]);
}

function _walkForSecrets(document, where, known) {
	if (typeof document === "string") {
		for (const secret of known) {
			if (document.includes(secret)) {
				throw new ContractError("integrity", "secret-leak",
					`${where} carries a live bearer value; §13 keeps the one `
					+ `deliberate secret off every durable surface, whatever `
					+ `field it arrives in`);
			}
		}
		return;
	}
	if (Array.isArray(document)) {
		for (const entry of document) _walkForSecrets(entry, where, known);
		return;
	}
	if (document === null || typeof document !== "object") return;
	for (const [key, value] of Object.entries(document)) {
		if (SECRET_FIELDS.has(key.toLowerCase())) {
			throw new ContractError("integrity", "secret-leak",
				`${where} carries ${key}; §13 keeps the one deliberate secret `
				+ `off every durable surface`);
		}
		_walkForSecrets(key, where, known);
		_walkForSecrets(value, where, known);
	}
}

/** Constant-time verifier comparison.
 *
 *  W2929 item 3: this was `!==`, which exits at the first differing byte —
 *  so the time taken tells a forger how much of the digest it already has
 *  right. The verifier is derived from the one deliberate secret and is
 *  compared on the path that decides whether authority is taken, which is
 *  the one comparison in this module worth spending a constant on.
 *
 *  `timingSafeEqual` requires equal lengths, so an unequal one is refused
 *  first. A length is not secret: the schema already fixes the digest's
 *  shape, so refusing on it reveals nothing a shape check would not.
 */
function sameVerifier(offered, stored) {
	if (typeof offered !== "string" || typeof stored !== "string") return false;
	const left = Buffer.from(offered, "utf8");
	const right = Buffer.from(stored, "utf8");
	if (left.length !== right.length) return false;
	return timingSafeEqual(left, right);
}

// §12 rule 14 (W4487): the binding check no schema can express.
//
// Schema proves the SHAPE — `null` for a decline, a string for an accept.
// It cannot prove the body names ONE ISSUED OFFER, and that is exactly what
// the superseded bearer requirement used to stand in for. A decline naming
// one offer while carrying another's attempt or Work terminates NEITHER.
export function validateOfferDecide(body, issued) {
	if (body?.decision !== "accept" && body?.decision !== "decline") {
		throw new ContractError("integrity", "schema",
			"offer.decide carries no decision");
	}
	if (body.decision === "decline") {
		if (body.claim_token !== null) {
			throw new ContractError("integrity", "schema",
				"a decline must not carry the claim bearer (W4487)");
		}
	} else if (typeof body.claim_token !== "string") {
		throw new ContractError("integrity", "schema",
			"an accept must carry the claim bearer");
	}
	for (const field of ["offer_id", "runtime_attempt_id"]) {
		if (body[field] !== issued[field]) {
			throw new ContractError("refused", "precondition",
				`offer.decide names ${field}=${body[field]}, and the issued `
				+ `offer records ${issued[field]}; a matching decision on a `
				+ `different binding terminates neither offer`);
		}
	}
	if (digest(body.work_ref) !== digest(issued.work_ref)) {
		throw new ContractError("refused", "precondition",
			"offer.decide names a different Work than the issued offer");
	}
	if (!issued.verifier_unspent) {
		throw new ContractError("refused", "precondition",
			"the offer verifier is already spent; it is single-use across "
			+ "acceptance, decline and expiry alike");
	}
	if (typeof body.reason !== "string" || body.reason.length === 0) {
		throw new ContractError("integrity", "schema",
			"offer.decide carries no reason, and the reason is a durable "
			+ "operand that rides the operation signature");
	}
	// The bearer's own proof of possession, for an ACCEPT only. Decline is
	// authorized by the binding above; acceptance is about to TAKE authority
	// and proves possession of the secret.
	if (body.decision === "accept"
			&& !sameVerifier(tokenVerifier(body.claim_token),
			                 issued.verifier)) {
		throw new ContractError("refused", "precondition",
			"the presented bearer does not match this offer's verifier");
	}
	return body.decision;
}

export function validateErrorBody(body) {
	const codes = ERROR_CODES[body?.category];
	if (!codes) {
		throw new ContractError("integrity", "schema",
			`${body?.category} is not a 1.0 error category`);
	}
	if (!codes.includes(body?.code)) {
		throw new ContractError("integrity", "schema",
			`${body.code} does not belong to the ${body.category} category`);
	}
}

// The whole envelope check, in the order a receiver may trust things: the
// body digest BEFORE any body field is read (§5), then the operation
// signature before the operation is journalled (§12 rule 9), then the
// semantic rules that need the body.
export function validateEnvelope(envelope) {
	if (envelope?.protocol !== PROTOCOL) {
		throw new ContractError("integrity", "schema",
			`not a ${PROTOCOL} frame`);
	}
	if (envelope.version?.major !== VERSION.major
			|| envelope.version?.minor !== VERSION.minor) {
		throw new ContractError("refused", "unsupported-version",
			`this manager speaks exactly ${VERSION.major}.${VERSION.minor}`);
	}
	// THE SCHEMA FIRST, before any field below is read. Everything after
	// this line may assume required members exist, enums are closed and the
	// message type means what it says.
	const owned = validateAgainstSchema(envelope, "control envelope");
	verifyBodyDigest(owned);
	verifyOperationSignature(owned);
	const body = owned.body;
	if (Object.hasOwn(body ?? {}, "work_ref") && body.work_ref !== null) {
		validateWorkRef(body.work_ref);
	}
	if (Object.hasOwn(body ?? {}, "assignment_ref") && body.assignment_ref !== null) {
		validateWorkRef(body.assignment_ref.work_ref);
	}
	if (owned.kind === "control.error") validateErrorBody(body);
	return owned;
}

// ---------------------------------------------------------------------------
// §12 manifest trust entry
// ---------------------------------------------------------------------------
//
// Round-3 review [P1]: this did not exist. The module header promised exact
// schema AND semantic validation below orchestration, and the AJV setup above
// justified leaving `format: "uri"` assertions off by naming a `validateUri`
// that "enforces below" — a helper nothing had written. So a copy of the
// frozen valid manifest carrying
// `https://source.invalid/archive?token=secret` passed every check this
// module offered. A secret-bearing durable locator was accepted at the exact
// boundary the foundation says it closes, and the gap was visible only in a
// comment's promise.
//
// These are the PURE document rules — the ones decidable from the bytes in
// front of you. Rule 2 (live assignment generation) and rule 11 (observation
// monotonicity) are deliberately absent: both need state this slice has no
// orchestration to hold, and they stay named in their own pending items
// rather than half-implemented here.

// §3.3. A destination is a logical role inside one private workspace, so a
// path that could leave it is refused rather than normalized — normalizing
// an attacker's path silently accepts what it was trying to say.
export function validateRelativePath(path, where = "path") {
	if (typeof path !== "string" || path.length === 0
			|| path.includes("\\") || path.includes("\0")
			|| path.startsWith("/")
			|| path.split("/").some((segment) =>
				segment === "" || segment === "." || segment === "..")) {
		throw new ContractError("integrity", "path",
			`${where} ${JSON.stringify(path)} is not a normalized `
			+ `POSIX-relative workspace path`);
	}
	return path;
}

// §12 rule 4, and §3.3's reason for it: a query string is where signed
// credentials and unstable selection parameters live, so a durable source
// locator may not carry one AT ALL. That is strictly more than `format:
// "uri"` asserts, which is why the format assertion stays off above.
export function validateUri(uri, where = "uri") {
	if (typeof uri !== "string" || uri.length === 0) {
		throw new ContractError("integrity", "schema",
			`${where} is not a URI`);
	}
	// Read the rule off the ORIGINAL TEXT first. `new URL` normalizes, and
	// a rule about what a durable string may CONTAIN must not be decided
	// only by a parser's reconstruction of it.
	const scheme = /^[A-Za-z][A-Za-z0-9+.-]*:/.exec(uri);
	if (scheme === null || uri.startsWith("//")) {
		throw new ContractError("integrity", "schema",
			`${where} ${JSON.stringify(uri)} is not an absolute URI`);
	}
	if (uri.includes("?")) {
		throw new ContractError("integrity", "schema",
			`${where} contains a query; durable source URIs forbid queries `
			+ `because that is where signed credentials and unstable `
			+ `selection parameters ride (§12 rule 4)`);
	}
	if (uri.includes("#")) {
		throw new ContractError("integrity", "schema",
			`${where} contains a fragment (§12 rule 4)`);
	}
	// A PARSE FAILURE IS A REFUSAL.
	//
	// Round-4 review [P1]: this caught and ignored every parse error under
	// the belief that a failure meant an opaque scheme. `https://[` is not
	// opaque, it is a malformed hierarchical URI — and with AJV format
	// assertions deliberately off, nothing else was going to notice. §3.3
	// requires an absolute NORMALIZED URI, and a string the one available
	// parser cannot read is not that.
	//
	// Every valid form this contract uses parses, measured rather than
	// assumed: `artifact://`, `https://`, `file:///`, `urn:` and `mailto:`
	// all succeed, so the opaque cases lose nothing by being held to it.
	let parsed;
	try {
		parsed = new URL(uri);
	} catch {
		throw new ContractError("integrity", "schema",
			`${where} ${JSON.stringify(uri)} is not a parseable absolute `
			+ `URI; a locator this build cannot read is never trusted `
			+ `state (§3.3)`);
	}
	// Userinfo needs the parse: it is only userinfo when it sits before the
	// authority's `@`, and `mailto:a@b` is not that.
	if (parsed.username !== "" || parsed.password !== "") {
		throw new ContractError("integrity", "schema",
			`${where} carries userinfo; a durable locator never carries a `
			+ `credential (§12 rule 4)`);
	}
	return uri;
}

// §3.3 says entries sort BYTEWISE, and JavaScript `<` does not.
//
// Round-4 review [P1]: `<` compares UTF-16 code units. `"\u{10000}.txt"`
// begins with the surrogate 0xD800 and sorts BELOW `"\uE000.txt"` there,
// while its UTF-8 bytes begin 0xF0 and sort ABOVE. So a list the contract
// calls unsorted was accepted, and this is a cross-language seal boundary:
// two conforming readers disagreeing about canonical tree order is exactly
// the failure a seal exists to prevent. The model implements byte order;
// so does this now.
function _bytewise(left, right) {
	return Buffer.compare(Buffer.from(left, "utf8"),
	                      Buffer.from(right, "utf8"));
}

// §12 rule 6. The aggregates are not decoration: a consumer that trusted
// `entry_count`/`total_bytes` without checking them against the entries
// would be trusting a claim about a tree it also holds.
export function validateContentManifest(content, where = "content manifest") {
	const entries = content.entries;
	const paths = entries.map((entry) => entry.path);
	paths.forEach((path, index) =>
		validateRelativePath(path, `${where} entry ${index}`));
	for (let at = 1; at < paths.length; at += 1) {
		// Bytewise sorted AND unique, in one pass: equality compares zero,
		// so a duplicate is caught here too.
		if (!(_bytewise(paths[at - 1], paths[at]) < 0)) {
			throw new ContractError("integrity", "schema",
				`${where} entries are not sorted bytewise and unique at `
				+ `${JSON.stringify(paths[at])}`);
		}
	}
	if (content.entry_count !== entries.length) {
		throw new ContractError("integrity", "schema",
			`${where} declares ${content.entry_count} entries and carries `
			+ `${entries.length}`);
	}
	const total = entries.reduce((sum, entry) => sum + entry.bytes, 0);
	if (content.total_bytes !== total) {
		throw new ContractError("integrity", "schema",
			`${where} declares ${content.total_bytes} bytes and its entries `
			+ `total ${total}`);
	}
	if (content.tree_digest !== digest(entries)) {
		throw new ContractError("integrity", "digest",
			`${where} tree digest does not recompute over the canonical `
			+ `ordered entry array (§3.3)`);
	}
	return content;
}

// §12 rule 5 for a manifest: the digest covers the whole document with the
// `manifest_digest` member OMITTED — not set to null, not set to the empty
// string, which are different documents with different canonical bytes.
export function verifyManifestDigest(document, where = "manifest") {
	const { manifest_digest: declared, ...rest } = document;
	if (declared !== digest(rest)) {
		throw new ContractError("integrity", "digest",
			`${where} digest does not recompute over its canonical bytes `
			+ `with manifest_digest omitted`);
	}
}

function _overlap(left, right) {
	return left === right
		|| left.startsWith(`${right}/`) || right.startsWith(`${left}/`);
}

// Every nested object that IS one, at any depth — the same walk shape as the
// secret check, and for the same reason: the rule is about what the document
// contains, not about where a current schema revision happens to put it.
function* _shaped(value, required) {
	if (Array.isArray(value)) {
		for (const entry of value) yield* _shaped(entry, required);
		return;
	}
	if (value === null || typeof value !== "object") return;
	if (required.every((key) => Object.hasOwn(value, key))) yield value;
	for (const child of Object.values(value)) yield* _shaped(child, required);
}

const ARTIFACT_REF_KEYS =
	["artifact_id", "media_type", "bytes", "content_digest", "locator"];
const CONTENT_MANIFEST_KEYS =
	["entries", "entry_count", "total_bytes", "tree_digest"];

/** THE trust entry for a durable manifest: schema first, then §12.
 *
 *  Schema-first for the reason the envelope entry is: every rule below
 *  reads members, and reading a member the schema has not established is
 *  how the round-2 bypass happened.
 *
 *  Returns an INDEPENDENTLY OWNED copy, like `validateAgainstSchema` — a
 *  validated document a caller can still mutate is a time-of-check alias
 *  wearing the word "validated". */
export function validateManifest(document, definition = "inputManifest",
                                 what = "input manifest") {
	const owned = validateSchemaFragment(
		structuredClone(document), definition, what);
	verifyManifestDigest(owned, what);
	// §13 before the rest: a document carrying a secret is refused as such
	// rather than as whatever structural fault is also in it.
	assertNoDurableSecret(owned, what);
	if (Object.hasOwn(owned, "work_ref")) validateWorkRef(owned.work_ref);
	if (owned.assignment_ref != null) {
		validateWorkRef(owned.assignment_ref.work_ref);
		if (!(owned.assignment_ref.generation >= 1)) {
			throw new ContractError("integrity", "schema",
				`${what} carries assignment generation `
				+ `${owned.assignment_ref.generation}; a generation is `
				+ `positive (§12 rule 2)`);
		}
	}
	// §12 rule 8's decidable half. Whether the bytes match is a collection-
	// time fact this slice cannot reach; that the REFERENCE is well formed
	// and its locator carries no credential is decidable here, and is the
	// half that keeps a secret out of the durable document.
	for (const artifact of _shaped(owned, ARTIFACT_REF_KEYS)) {
		validateUri(artifact.locator,
			`${what} artifact ${artifact.artifact_id} locator`);
	}
	for (const content of _shaped(owned, CONTENT_MANIFEST_KEYS)) {
		validateContentManifest(content, `${what} content manifest`);
	}
	if (owned.schema === "baton.worker-manifest/input") {
		_validateInputManifest(owned, what);
	}
	return owned;
}

function _validateInputManifest(owned, what) {
	const { sources, outputs } = owned;
	const names = [...sources, ...outputs].map((item) => item.name);
	if (new Set(names).size !== names.length) {
		throw new ContractError("integrity", "schema",
			`${what} reuses an input/output name; names are unique across `
			+ `both (§12 rule 3)`);
	}
	const destinations = [...sources.map((source) => source.destination),
	                      ...outputs.map((output) => output.path)];
	destinations.forEach((path, index) =>
		validateRelativePath(path, `${what} destination ${index}`));
	for (let left = 0; left < destinations.length; left += 1) {
		for (let right = left + 1; right < destinations.length; right += 1) {
			// OVERLAP, not equality. A declared output inside a source
			// directory would have the worker writing into material the
			// manifest also says was delivered — and the seal over that
			// tree would stop describing what is on disk.
			if (_overlap(destinations[left], destinations[right])) {
				throw new ContractError("integrity", "path",
					`${what} destinations `
					+ `${JSON.stringify(destinations[left])} and `
					+ `${JSON.stringify(destinations[right])} overlap `
					+ `(§12 rule 3)`);
			}
		}
	}
	for (const source of sources) {
		validateUri(source.uri, `${what} source ${source.name} uri`);
		// §12 rule 7: a sha1 base revision under a sha256 repository is not
		// a shorter digest, it is a different object namespace.
		if (source.type === "git"
				&& source.object_format !== source.base_revision.algorithm) {
			throw new ContractError("integrity", "schema",
				`${what} source ${source.name} declares object format `
				+ `${source.object_format} and a `
				+ `${source.base_revision.algorithm} base revision `
				+ `(§12 rule 7)`);
		}
	}
}
