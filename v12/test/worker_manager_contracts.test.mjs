// W2929: the frozen worker-control 1.0 boundary, in product code.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// These are the cases the acceptance boundary calls "schema byte identity,
// exact 1.0 negotiation, canonical vectors, seals, closed error pairs and
// semantic negatives". They run against the SEALED product copy of the
// schema and against the design record's own vectors, so the product and
// the frozen contract cannot drift apart quietly.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
	CAPABILITIES, ContractError, ERROR_CODES, GOLDEN_BEARER, GOLDEN_VERIFIER,
	SCHEMA, SCHEMA_BYTES, SCHEMA_ERROR_CATEGORIES, SCHEMA_ERROR_CODES,
	canonicalBytes, digest, negotiate, operationSignature, validateSchemaFragment,
	operationSignaturePayload, requireNegotiated, tokenVerifier,
	assertNoDurableSecret, validateEnvelope, validateOfferDecide,
	validateManifest, validateUri, validateRelativePath, verifyManifestDigest,
	validateContentManifest, rememberSecret, forgetSecret, withSecret,
} from "../src/worker_manager/contracts.mjs";

// The frozen rule, in the tests too: a manifest seals over itself with the
// digest member OMITTED. Every fixture below that alters a manifest reseals
// it through this, so a case never passes or fails for the digest when it is
// about something else.
const manifestDigestOf = ({ manifest_digest: _sealed, ...rest }) => digest(rest);

const HERE = dirname(fileURLToPath(import.meta.url));
const RECORD = join(HERE, "..", "..", "work", "records", "2026", "08",
	"finding-v12-isolated-agent-workers", "findings",
	"finding-v12-worker-contract", "findings",
	"finding-worker-control-api-manifests");

// -- the seal ---------------------------------------------------------------

test("W2929: the product schema is byte-identical to the frozen asset", () => {
	// A paraphrase would be a second, quieter contract: the first time the
	// two disagreed, the design record would say one thing and the running
	// manager another, and only the running one would matter.
	const frozen = readFileSync(
		join(RECORD, "schema", "worker-control-1.0.schema.json"));
	assert.deepEqual(SCHEMA_BYTES, frozen,
		"the sealed product copy drifted from the frozen design asset");
	assert.equal(SCHEMA.$id, "urn:baton:worker-control:1.0");
});

test("W2929: the closed error pairing accounts for the frozen vocabulary", () => {
	// The schema carries the two enums FLAT and does not pair them — which
	// is why §12 makes the pairing a semantic rule. This is what stops the
	// written-out pairing from drifting: a code added to the frozen schema
	// without a category fails here rather than becoming unmappable.
	const paired = Object.values(ERROR_CODES).flat();
	assert.deepEqual([...paired].sort(), [...SCHEMA_ERROR_CODES].sort());
	assert.deepEqual(Object.keys(ERROR_CODES).sort(),
	                 [...SCHEMA_ERROR_CATEGORIES].sort());
	assert.equal(paired.length, new Set(paired).size,
		"one code belongs to two categories");
});

// -- §3.2 canonical bytes ---------------------------------------------------

test("W2929: canonicalization orders members and refuses what §3.2 forbids", () => {
	assert.equal(canonicalBytes({ b: 1, a: 2 }).toString(), '{"a":2,"b":1}');
	assert.equal(canonicalBytes({ "é": [1, null, true] }).toString(),
	             '{"é":[1,null,true]}');
	// Nested order too, not only the top level.
	assert.equal(canonicalBytes({ z: { y: 1, x: 2 } }).toString(),
	             '{"z":{"x":2,"y":1}}');
	for (const forbidden of [1.5, Number.NaN, Infinity, -0.5, 2 ** 60,
	                         // Review 2026-08-22 [P1]: `-1` serialized as
	                         // `-1` and `-0` as `0`, both forbidden by §3.2
	                         // and both acquiring digests under a function
	                         // presented as the canonical trust boundary.
	                         -1, -0]) {
		assert.throws(() => canonicalBytes({ value: forbidden }),
			(error) => error instanceof ContractError
				&& error.category === "integrity", String(forbidden));
	}
	// A lone surrogate must FAIL rather than be repaired into something
	// digestible; RFC 8785 says so and `JSON.stringify` would have escaped it.
	assert.throws(() => canonicalBytes({ value: "a\uD800b" }),
		(error) => error.code === "schema" && /surrogate/.test(error.message));
	// Member names are strings too. Checking values but handing keys straight
	// to JSON.stringify gives malformed Unicode a canonical digest merely by
	// moving it to the left side of a colon.
	assert.throws(() => canonicalBytes({ ["a\uD800b"]: 1 }),
		(error) => error.code === "schema" && /surrogate/.test(error.message));
	// A sparse array is not a JSON array: its holes would serialize as
	// `null` and silently change the document being digested.
	const sparse = [1, , 3];                                    // eslint-disable-line no-sparse-arrays
	assert.throws(() => canonicalBytes({ value: sparse }),
		(error) => error.code === "schema" && /hole/.test(error.message));
	// And a value that is not a plain object would serialize as something
	// other than what the caller meant.
	for (const exotic of [new Date(0), new Map(), /re/]) {
		assert.throws(() => canonicalBytes({ value: exotic }),
			(error) => error.code === "schema", String(exotic));
	}
	// Two documents differing only in member ORDER have one digest; two
	// differing in a value do not.
	assert.equal(digest({ a: 1, b: 2 }), digest({ b: 2, a: 1 }));
	assert.notEqual(digest({ a: 1, b: 2 }), digest({ a: 1, b: 3 }));
});

// -- the verifier -----------------------------------------------------------

test("W2929: the claim-token verifier is W151's ONE derivation", () => {
	// The golden pair, against a LITERAL. A recomputation of the same
	// expression would agree with any derivation, including a wrong one —
	// which is exactly how the two design models disagreed for a round.
	assert.equal(tokenVerifier(GOLDEN_BEARER), GOLDEN_VERIFIER);
	// The bearer's own bytes, not a JSON encoding of them.
	assert.notEqual(tokenVerifier(GOLDEN_BEARER), digest(GOLDEN_BEARER));
	for (const awkward of ['a"b'.padEnd(32, "c"), "a\\b".padEnd(32, "c"),
	                       "é".padEnd(32, "c")]) {
		assert.equal(tokenVerifier(awkward).length, "sha256:".length + 64);
		assert.notEqual(tokenVerifier(awkward), digest(awkward), awkward);
	}
	assert.throws(() => tokenVerifier(null), ContractError);
});

test("W2929: the product agrees with the design model's golden pair", () => {
	// Cross-checked against the record rather than asserted twice here: the
	// value is pinned in W151's model and in worker-control's, and the
	// conformance package asserts those two agree. This is the third copy
	// and it is checked against the same literal.
	const model = readFileSync(
		join(RECORD, "evidence", "contract_model.py"), "utf8");
	assert.ok(model.includes(GOLDEN_VERIFIER.slice("sha256:".length, 60)),
		"the product's golden verifier is not the one pinned in the model");
	assert.ok(model.includes('GOLDEN_BEARER = "x" * 43'));
});

// -- §4.2 the operation signature -------------------------------------------

const WORK_REF = {
	authority_uuid: "43c55d4b1234567890abcdef12345678",
	work_id: "43c55d4b-W1439",
};

function declineBody(overrides = {}) {
	return {
		offer_id: "offer-1", runtime_attempt_id: "attempt-1",
		// A COPY: the ownership case below mutates a caller's body to prove
		// the validated value is independent, and sharing the module-level
		// constant would have made that mutation corrupt every later case.
		work_ref: structuredClone(WORK_REF), decision: "decline",
		reason: "the worker endpoint has no free runtime capacity",
		claim_token: null, ...overrides,
	};
}

function envelope(kind, body, { message_type = "command", operation } = {}) {
	return {
		protocol: "baton.worker-control",
		version: { major: 1, minor: 0 },
		message_type, kind,
		message_id: `message-${kind}`,
		correlation_id: message_type === "reply" ? "request-1" : null,
		sent_at: "2026-08-22T16:00:00.000Z",
		sender: { role: "worker-manager", instance_id: "manager-1" },
		operation: operation === undefined
			? { operation_id: `operation-${kind}`,
			    signature_digest: operationSignature(kind, body) }
			: operation,
		body_digest: digest(body),
		body,
		extensions: {},
	};
}

test("W2929: the signature covers the KIND, so it is never the body digest", () => {
	const body = declineBody();
	assert.notEqual(operationSignature("offer.decide", body), digest(body));
	// `output.freeze` and `output.collect` carry the same body: one
	// operation id reused across the two must collide rather than replay.
	const output = { assignment_ref: { work_ref: WORK_REF, participant: "p",
	                                   generation: 7 },
	                 runtime_attempt_id: "attempt-1", result_id: "result-1",
	                 output_names: ["proposal"], result_manifest_digest: digest(1),
	                 policy_digest: digest(2) };
	assert.notEqual(operationSignature("output.freeze", output),
	                operationSignature("output.collect", output));
});

test("W2929: a bearer rides as its verifier, and null stays null", () => {
	const accepting = declineBody({ decision: "accept",
	                                claim_token: GOLDEN_BEARER });
	const payload = operationSignaturePayload("offer.decide", accepting);
	assert.ok(!Object.hasOwn(payload.operands, "claim_token"));
	assert.equal(payload.operands.claim_token_verifier, GOLDEN_VERIFIER);
	// The payload is safe to persist, which is the whole reason for it.
	assertNoDurableSecret(payload);
	// A different token is a different operation, not an exact replay.
	assert.notEqual(
		operationSignature("offer.decide", accepting),
		operationSignature("offer.decide",
			declineBody({ decision: "accept", claim_token: "y".repeat(43) })));
	// A decline commits to the ABSENCE of a bearer as positively.
	assert.equal(operationSignaturePayload("offer.decide", declineBody())
		.operands.claim_token_verifier, null);
});

test("W2929: a stale signature refuses before the operation is journalled", () => {
	// The reviewer's reproduction from W4487, on the product path: change
	// the durable reason, recompute ONLY the body digest, keep the old
	// signature. A manager journalling by it would replay the first decline
	// against conflicting prose.
	const frame = envelope("offer.decide", declineBody());
	const stale = frame.operation.signature_digest;
	frame.body.reason = "an entirely different durable reason";
	frame.body_digest = digest(frame.body);
	assert.throws(() => validateEnvelope(frame), (error) =>
		error instanceof ContractError && error.category === "integrity"
		&& error.code === "digest");
	assert.equal(frame.operation.signature_digest, stale);
});

test("W2929: a reply echoes its request's signature and is not recomputed", () => {
	// §5: a reply carries the same operation as the request it answers, so
	// its signature is the REQUEST's and its body is a result. The exemption
	// is keyed on message_type, and the same document sent as a COMMAND is
	// refused — which is what keeps it an exemption rather than a hole.
	const opaque = { operation_id: "operation-1", signature_digest: digest("x") };
	const reply = envelope("operation.reply",
		{ status: "committed", result_schema: "offer-decide-result",
		  result_digest: digest(1), result_artifact: null },
		{ message_type: "reply", operation: opaque });
	assert.doesNotThrow(() => validateEnvelope(reply));
	// The same document relabelled a COMMAND is refused — by the schema
	// itself, which binds the kind to its message type, so the exemption is
	// not something a relabelling can walk into.
	const asCommand = { ...reply, message_type: "command", correlation_id: null };
	assert.throws(() => validateEnvelope(asCommand), (error) =>
		error.code === "schema");
	// Re-review 2026-08-22 [P1]: there is no forgeable proof bit any more.
	// `verifyOperationSignature` is module-private and the exemption follows
	// from a brand only the validator can apply, so there is no lower-level
	// door to walk through.
	assert.equal(typeof globalThis.verifyOperationSignature, "undefined");
});

test("W2929: schema proof cannot be self-attested", async () => {
	// The reviewer's case, kept and made unsatisfiable rather than deleted.
	// It called the exported helper with `schemaProven: true`, which was not
	// evidence that AJV had run and recreated the misspelled-discriminator
	// exemption through a lower-level door.
	//
	// There is no such door now: the helper is module-private and the
	// exemption follows from a brand only the validator applies. So the
	// property is asserted two ways — the export is gone, and the frame the
	// reviewer forged is refused by the one entry that remains.
	const module = await import("../src/worker_manager/contracts.mjs");
	assert.equal(module.verifyOperationSignature, undefined,
		"a forgeable proof bit is still reachable from outside");
	const frame = envelope("offer.decide", declineBody());
	frame.body.reason = "different durable operands under the stale signature";
	frame.body_digest = digest(frame.body);
	frame.message_type = "commmand";
	assert.throws(() => validateEnvelope(frame), (error) =>
		error.code === "schema",
		"the forged frame reached the reply exemption");
	// And a document that merely LOOKS validated is not: the brand is
	// identity-based, so a copy of a validated envelope is re-validated on
	// its own merits rather than inheriting the original's standing.
	const good = validateEnvelope(envelope("offer.decide", declineBody()));
	const impostor = { ...structuredClone(good), message_type: "commmand" };
	assert.throws(() => validateEnvelope(impostor), (error) =>
		error.code === "schema");
});

test("W2929: a MISSPELLED discriminator cannot buy the reply exemption", () => {
	// The review's exact reproduction, and the reason schema validation
	// became a blocking prerequisite: one letter turned a mutating command
	// with a stale operation signature into the reply exemption, before
	// anything had proved it was a reply.
	const frame = envelope("offer.decide", declineBody());
	frame.body.reason = "an entirely different durable reason";
	frame.body_digest = digest(frame.body);
	frame.message_type = "commmand";
	assert.throws(() => validateEnvelope(frame), (error) =>
		error instanceof ContractError && error.code === "schema");
});

test("W2929: the schema is proved before any semantic helper reads a field", () => {
	// Not only unknown extra fields: MISSING required members, closed enums
	// and mistyped values were all being read by the semantic helpers before
	// anything established them.
	const base = () => envelope("offer.decide", declineBody());
	const missing = base();
	delete missing.sender;
	assert.throws(() => validateEnvelope(missing), (error) =>
		error.code === "schema" && /sender|required/.test(error.message));
	const extra = base();
	extra.body.optimistic = true;
	extra.body_digest = digest(extra.body);
	assert.throws(() => validateEnvelope(extra), (error) =>
		error.code === "schema");
	const mistyped = base();
	mistyped.body.reason = 7;
	mistyped.body_digest = digest(mistyped.body);
	assert.throws(() => validateEnvelope(mistyped), (error) =>
		error.code === "schema");
	const badEnum = base();
	badEnum.body.decision = "maybe";
	badEnum.body_digest = digest(badEnum.body);
	assert.throws(() => validateEnvelope(badEnum), (error) =>
		error.code === "schema");
});

test("W2929: a validated envelope is a copy, not a caller-owned alias", () => {
	// This function is the trust entry. Returning the untrusted object means a
	// caller can mutate fields after schema/digest/signature validation and the
	// value downstream code regards as validated changes underneath it.
	const frame = envelope("offer.decide", declineBody());
	const validated = validateEnvelope(frame);
	assert.notStrictEqual(validated, frame);
	assert.notStrictEqual(validated.body, frame.body);
	frame.body.reason = "mutated after the trust boundary";
	assert.equal(validated.body.reason,
		"the worker endpoint has no free runtime capacity");
});

test("W2929: canonicalization refuses invalid Unicode in a member NAME", () => {
	// Re-review 2026-08-22 [P1]: the surrogate check ran on string VALUES,
	// so moving the same malformed Unicode into a key made it digestible.
	// RFC 8785's invalid-Unicode failure is not side-dependent.
	assert.throws(() => canonicalBytes({ value: "a\uD800b" }),
		(error) => error.code === "schema" && /surrogate/.test(error.message));
	assert.throws(() => canonicalBytes({ "a\uD800b": 1 }),
		(error) => error.code === "schema" && /member name/.test(error.message));
	assert.throws(() => canonicalBytes({ nested: { "\uDC00": 1 } }),
		(error) => error.code === "schema" && /member name/.test(error.message));
});

test("W2929: the negotiation POLICY is held to the frozen constraints too", () => {
	// Re-review 2026-08-22 [P1]: the peer's hello was schema-proven and the
	// manager's own policy was not, so `"not-a-digest"` became trusted
	// negotiation state. Being local does not make a malformed identity a
	// certified profile.
	assert.throws(() => negotiate(hello(),
		{ limits: LIMITS, runtimeProfileDigest: "not-a-digest" }),
		(error) => error.code === "schema"
			&& /runtime profile digest/.test(error.message));
	assert.throws(() => negotiate(hello(),
		{ limits: { ...LIMITS, max_frame_bytes: -1 },
		  runtimeProfileDigest: PROFILE }),
		(error) => error.code === "schema" && /limits/.test(error.message));
	assert.throws(() => negotiate(hello(),
		{ ...POLICY, extensions: ["not an extension"] }),
		(error) => error.code === "schema");
	// The valid policy still forms a welcome.
	assert.doesNotThrow(() => negotiate(hello(), POLICY));
});

test("W2929: the validated value is INDEPENDENTLY OWNED", () => {
	// Re-review 2026-08-22 [P1]: the trust entry returned its input, so
	// after every check passed the caller could mutate the same body's
	// durable operands and the value downstream code regarded as validated
	// changed with it — a time-of-check/time-of-use alias.
	const caller = envelope("offer.decide", declineBody());
	const owned = validateEnvelope(caller);
	assert.notEqual(owned, caller);
	assert.notEqual(owned.body, caller.body);
	// Mutating the caller's copy, at the top level and at a NESTED member,
	// leaves the validated value alone.
	caller.body.reason = "changed after validation";
	caller.body.work_ref.work_id = "43c55d4b-W9999";
	caller.operation.signature_digest = digest("nonsense");
	assert.equal(owned.body.reason, declineBody().reason);
	assert.equal(owned.body.work_ref.work_id, WORK_REF.work_id);
	assert.equal(owned.operation.signature_digest,
	             operationSignature("offer.decide", declineBody()));
	// And the digest the checks ran against still describes the value that
	// came back.
	assert.equal(owned.body_digest, digest(owned.body));
});

test("W2929: the body digest is checked before any body field is trusted", () => {
	const frame = envelope("offer.decide", declineBody());
	frame.body.reason = "tampered";
	assert.throws(() => validateEnvelope(frame), (error) =>
		error.code === "digest");
});

// -- §2 negotiation ---------------------------------------------------------

const LIMITS = Object.freeze({ max_frame_bytes: 1048576,
	max_extension_bytes: 65536, max_artifact_bytes: 1073741824,
	max_manifest_entries: 10000, max_activity_bytes: 16000 });
const PROFILE = "sha256:" + "b".repeat(64);

function hello(overrides = {}) {
	return { role: "runtime-adapter",
	         supported_versions: [{ major: 1, minor: 0 }],
	         capabilities: ["core.errors", "core.runtime-lifecycle"],
	         extensions: [], limits: LIMITS,
	         runtime_profile_digest: PROFILE, ...overrides };
}

const POLICY = { limits: LIMITS, runtimeProfileDigest: PROFILE };

test("W2929: negotiation is EXACT and forms a valid frozen welcome", () => {
	// Review 2026-08-22 [P1]: this accepted a hello with neither `limits`
	// nor `runtime_profile_digest`, echoed every peer extension as though
	// it were selected, and returned no `effective_limits` — so its answer
	// could not itself validate as a `control.welcome` body.
	const { welcome } = negotiate(hello(), POLICY);
	assert.deepEqual(welcome.selected_version, { major: 1, minor: 0 });
	assert.deepEqual(welcome.capabilities,
	                 ["core.errors", "core.runtime-lifecycle"]);
	// The answer is a frozen welcome body, byte-valid against the schema.
	assert.doesNotThrow(() => validateSchemaFragment(welcome, "welcomeBody",
	                                                 "welcome"));
	// A later minor is not accepted by ignoring what it does not know. The
	// frozen schema pins the version constants, so a 1.1 offer cannot even
	// be EXPRESSED in a 1.0 hello — a stronger refusal than the version
	// check below it, and the reason that check now reads as a second line
	// rather than the first.
	assert.throws(() => negotiate(hello({
		supported_versions: [{ major: 1, minor: 1 }] }), POLICY), (error) =>
		error.code === "schema");
	// The version check is still reachable for a document the schema admits:
	// two versions offered, neither of them this one, is not a shape error.
	assert.throws(() => negotiate({ ...hello(), supported_versions: [] },
		POLICY), (error) => error.code === "schema");
	// Missing required members are refused by the schema, before anything
	// below reads them.
	for (const missing of ["limits", "runtime_profile_digest", "capabilities"]) {
		const partial = hello();
		delete partial[missing];
		assert.throws(() => negotiate(partial, POLICY), (error) =>
			error.code === "schema", missing);
	}
	// And a manager that cannot state its own policy cannot negotiate.
	assert.throws(() => negotiate(hello()), (error) =>
		error.code === "precondition");
	// The local profile digest is returned as trusted negotiation state even
	// though it rides outside `welcome`; it still has to satisfy the frozen
	// digest contract rather than bypassing the welcome fragment validator.
	assert.throws(() => negotiate(hello(), {
		...POLICY, runtimeProfileDigest: "not-a-digest",
	}), (error) => error.code === "schema");
	// A kind whose capability was not negotiated is refused, by name.
	assert.throws(() => requireNegotiated(welcome, "core.proposal",
	                                      "proposal.publish"), (error) =>
		error.code === "capability" && /proposal\.publish/.test(error.message));
});

test("W2929: an extension is SELECTED only if both sides implement it", () => {
	// "Selected" has to mean an intersection with something. Echoing the
	// peer's list claimed support this build does not have.
	const offered = hello({ extensions: ["org.example.metrics/1",
	                                     "org.example.not-implemented/1"] });
	const { welcome } = negotiate(offered,
		{ ...POLICY, extensions: ["org.example.metrics/1"] });
	assert.deepEqual(welcome.extensions, ["org.example.metrics/1"]);
	// With no local support, nothing is selected — not everything offered.
	assert.deepEqual(negotiate(offered, POLICY).welcome.extensions, []);
	// A malformed or duplicated extension is refused by the schema's own
	// pattern and uniqueness, before selection runs.
	for (const bad of [["not an extension"], ["org.example.metrics/1",
	                                          "org.example.metrics/1"]]) {
		assert.throws(() => negotiate(hello({ extensions: bad }), POLICY),
			(error) => error.code === "schema", JSON.stringify(bad));
	}
});

test("W2929: effective limits are the pair BOTH sides survive", () => {
	// Each bound says what its side can survive, so the answer is the
	// smaller. Returning the manager's own numbers would tell a peer to
	// send frames it has just said it cannot receive.
	const tight = { ...LIMITS, max_frame_bytes: 65536,
	                max_activity_bytes: 32000 };
	const { welcome } = negotiate(hello({ limits: tight }), POLICY);
	assert.equal(welcome.effective_limits.max_frame_bytes, 65536);
	assert.equal(welcome.effective_limits.max_activity_bytes, 16000);
	assert.deepEqual(Object.keys(welcome.effective_limits).sort(),
	                 Object.keys(LIMITS).sort());
});

// -- §12/§13 semantics ------------------------------------------------------

test("W2929: the durable-secret walk finds a bearer at any depth", () => {
	assertNoDurableSecret({ verifier: GOLDEN_VERIFIER, nested: { fine: 1 } });
	assert.throws(() => assertNoDurableSecret(
		{ decision: { claim_token: GOLDEN_BEARER } }), (error) =>
		error.code === "secret-leak");
	assert.throws(() => assertNoDurableSecret(
		{ list: [{ deep: { access_token: "x" } }] }), (error) =>
		error.code === "secret-leak");
});

test("W2929: an offer.decide binding names ONE issued offer", () => {
	const issued = { offer_id: "offer-1", runtime_attempt_id: "attempt-1",
	                 work_ref: WORK_REF, verifier: GOLDEN_VERIFIER,
	                 verifier_unspent: true };
	assert.equal(validateOfferDecide(declineBody(), issued), "decline");
	// A decline naming one offer while carrying another's attempt or Work
	// terminates NEITHER.
	for (const [field, value] of [["offer_id", "offer-2"],
	                              ["runtime_attempt_id", "attempt-2"]]) {
		assert.throws(() => validateOfferDecide(
			declineBody({ [field]: value }), issued), (error) =>
			error.category === "refused" && error.code === "precondition", field);
	}
	assert.throws(() => validateOfferDecide(declineBody({
		work_ref: { ...WORK_REF, work_id: "43c55d4b-W9999" } }), issued),
		(error) => error.code === "precondition");
	// The verifier is single-use across acceptance, decline and expiry.
	assert.throws(() => validateOfferDecide(declineBody(),
		{ ...issued, verifier_unspent: false }), /already spent/);
	// The reason is a durable operand, so its absence is a schema refusal.
	assert.throws(() => validateOfferDecide(declineBody({ reason: "" }), issued),
		/carries no reason/);
});

test("W2929: acceptance still proves possession; decline must not carry it", () => {
	const issued = { offer_id: "offer-1", runtime_attempt_id: "attempt-1",
	                 work_ref: WORK_REF, verifier: GOLDEN_VERIFIER,
	                 verifier_unspent: true };
	assert.equal(validateOfferDecide(
		declineBody({ decision: "accept", claim_token: GOLDEN_BEARER }), issued),
		"accept");
	// W4487 supersedes the bearer for DECLINE and changes nothing about
	// acceptance — the obvious wrong reading, refused in both directions.
	assert.throws(() => validateOfferDecide(
		declineBody({ claim_token: GOLDEN_BEARER }), issued),
		/must not carry the claim bearer/);
	assert.throws(() => validateOfferDecide(
		declineBody({ decision: "accept" }), issued),
		/must carry the claim bearer/);
	assert.throws(() => validateOfferDecide(
		declineBody({ decision: "accept", claim_token: "y".repeat(43) }), issued),
		/does not match this offer's verifier/);
});

test("W2929: an error body's code must belong to its category", () => {
	const body = { category: "integrity", code: "runtime-start",
	               summary: "mapped to the wrong portable category",
	               retry: "never", operation_state: "refused",
	               assignment_ref: null, runtime_attempt_id: null,
	               diagnostic_artifact: null };
	assert.throws(() => validateEnvelope(envelope("control.error", body,
		{ message_type: "reply", operation: null })), /does not belong/);
	body.code = "digest";
	assert.doesNotThrow(() => validateEnvelope(envelope("control.error", body,
		{ message_type: "reply", operation: null })));
});

test("W2929: a Work id must carry its authority's prefix", () => {
	const frame = envelope("offer.decide", declineBody({
		work_ref: { authority_uuid: "43c55d4b1234567890abcdef12345678",
		            work_id: "deadbeef-W1" } }));
	assert.throws(() => validateEnvelope(frame), /does not carry its authority/);
});

test("W2929: the frozen decline vector validates unchanged", () => {
	// The record's own canonical vector, through the PRODUCT validator. If
	// the two ever disagree about one document, this is where it shows.
	const vectors = JSON.parse(readFileSync(
		join(RECORD, "evidence", "vectors.json"), "utf8"));
	const vector = vectors.valid.find((entry) =>
		entry.name === "offer-decide-decline-carries-no-bearer");
	assert.ok(vector, "the frozen decline vector is gone");
	assert.doesNotThrow(() => validateEnvelope(structuredClone(vector.document)));
	assert.equal(vector.document.operation.signature_digest,
		operationSignature(vector.document.kind, vector.document.body),
		"the product recomputes a different signature than the frozen vector");
});


// -- §12 manifest trust entry -------------------------------------------------

// Round-3 review [P1]. The frozen record carries the manifest vectors and
// their two SEMANTIC invalid cases; the product had no entry to drive them
// through, so nothing compared the two. These read the record directly, the
// way the decline-vector case above does: a divergence between the frozen
// contract and this implementation shows up here rather than in orchestration.
function manifestVectors() {
	return JSON.parse(readFileSync(
		join(RECORD, "evidence", "vectors.json"), "utf8"));
}

function validManifest() {
	const vector = manifestVectors().valid.find((entry) =>
		entry.name === "input-manifest-directory-and-declared-output");
	assert.ok(vector, "the frozen input-manifest vector is gone");
	return structuredClone(vector.document);
}

// The record expresses an invalid case as a PATCH against a named valid one,
// so the mutation applied here is the record's own, not a paraphrase of it.
//
// AND IT RESEALS. Mutation-checking caught this: without the reseal both
// semantic vectors were refused by `verifyManifestDigest` — a patched
// document no longer matches its declared `manifest_digest` — so the cases
// passed while proving nothing about the rules they name. Removing the whole
// input-manifest semantic block left them green. A vector that must witness
// "destinations overlap" has to reach the destination check.
function patched(patch) {
	const document = validManifest();
	for (const [dotted, value] of Object.entries(patch)) {
		const path = dotted.split(".");
		const last = path.pop();
		let node = document;
		for (const step of path) node = node[step];
		node[last] = value;
	}
	document.manifest_digest = manifestDigestOf(document);
	return document;
}

test("W2929: the frozen input manifest validates through the product entry", () => {
	const document = validManifest();
	const owned = validateManifest(document);
	assert.deepEqual(owned, document,
		"the trust entry changed the document it validated");
	// OWNED, like the envelope entry: mutating the input afterwards must not
	// reach the value the caller was told is validated.
	document.sources[0].uri = "https://elsewhere.invalid/archive";
	assert.equal(owned.sources[0].uri, "artifact://inputs/source-1");
});

test("W2929: the record's semantic-invalid manifests are refused", () => {
	// These two are the exact cases the frozen record labels `semantic` —
	// the schema deliberately cannot express either, which is why the trust
	// entry has to.
	const vectors = manifestVectors();
	for (const name of ["durable-source-query-refused",
	                    "manifest-overlapping-input-and-output"]) {
		const vector = vectors.invalid.find((entry) => entry.name === name);
		assert.ok(vector, `the frozen ${name} vector is gone`);
		assert.equal(vector.layer, "semantic",
			`${name} is no longer a semantic case; this test is about the `
			+ `rules the schema cannot reach`);
		const document = patched(vector.patch);
		// The SCHEMA still accepts it. That is the whole point: without the
		// semantic entry these documents are indistinguishable from valid.
		assert.doesNotThrow(() =>
			validateSchemaFragment(structuredClone(document), "inputManifest",
				"input manifest"),
			`${name} is now a schema refusal, so it no longer witnesses the `
			+ `semantic boundary`);
		// The refusal must be the one the record NAMES. "refused somehow" is
		// what the missing reseal was quietly giving.
		assert.throws(() => validateManifest(document),
			(error) => error instanceof ContractError
				&& new RegExp(vector.expected.split(" ").at(-1), "i")
					.test(error.message),
			`${name} was not refused for ${vector.expected}`);
	}
});

test("W2929: a durable locator carrying a credential is refused", () => {
	// §12 rule 4 is stronger than `format: "uri"`, which is why format
	// assertions are off and this exists instead. A query is refused because
	// that is where a signed credential rides — the frozen vector's own
	// `?token=secret` is the case.
	// MIGRATED by the canonical-grammar ruling: the two authority-less forms
	// were expected to say "absolute", and the grammar refuses them earlier and
	// for a more precise reason -- they are not `scheme://authority` at all.
	// The refusals themselves are retained.
	for (const [uri, why] of [
			["https://source.invalid/archive?token=secret", /query/],
			["https://user:pass@source.invalid/archive", /userinfo/],
			["https://source.invalid/archive#frag", /fragment/],
			["/not/absolute", /canonical locator/],
			["//source.invalid/archive", /canonical locator/]]) {
		assert.throws(() => validateUri(uri, "locator"), why, uri);
	}
	assert.doesNotThrow(() => validateUri("artifact://inputs/source-1"));
	assert.doesNotThrow(() => validateUri("https://source.invalid/archive"));
});

test("W2929 review: a parser-invalid absolute URI is never trusted", () => {
	// `format: uri` is deliberately disabled in AJV, so the semantic entry is
	// the only parser boundary. A scheme prefix alone is not an absolute,
	// normalized URI; swallowing URL's parse failure admits malformed input.
	const document = validManifest();
	document.sources[0].uri = "https://[";
	document.manifest_digest = manifestDigestOf(document);
	assert.doesNotThrow(() =>
		validateSchemaFragment(structuredClone(document), "inputManifest",
			"input manifest"),
		"the schema now refuses this, so it no longer witnesses the semantic URI boundary");
	assert.throws(() => validateManifest(document),
		(error) => error instanceof ContractError && error.code === "schema");
});

test("W2929: an artifact locator is checked wherever it sits", () => {
	// The walk, not a field list: the human contract's locator is nested in
	// a member no §12 rule names, and it is exactly as durable as the
	// sources'. A rule keyed on known paths would miss it.
	//
	// USERINFO is the mutation, deliberately. The schema's locator pattern
	// already excludes `?` and `#`, so a query here would be a schema
	// refusal and would witness nothing about §12; a credential in the
	// authority passes that pattern and only rule 4 catches it.
	const document = validManifest();
	document.human_contract.locator = "https://user:pass@contracts.invalid/hc-1";
	document.manifest_digest = manifestDigestOf(document);
	assert.doesNotThrow(() =>
		validateSchemaFragment(structuredClone(document), "inputManifest",
			"input manifest"),
		"the schema now refuses this, so it no longer witnesses rule 4");
	assert.throws(() => validateManifest(document), /userinfo/);
});

test("W2929: content-manifest aggregates and the tree seal are recomputed", () => {
	// Each half separately: a consumer trusting the declared count or total
	// would be trusting a claim about a tree it is also holding.
	const count = validManifest();
	count.sources[0].content_manifest.entry_count = 2;
	count.manifest_digest = manifestDigestOf(count);
	assert.throws(() => validateManifest(count), /declares 2 entries/);

	const bytes = validManifest();
	bytes.sources[0].content_manifest.total_bytes = 5;
	bytes.manifest_digest = manifestDigestOf(bytes);
	assert.throws(() => validateManifest(bytes), /declares 5 bytes/);

	const tree = validManifest();
	tree.sources[0].content_manifest.entries[0].bytes = 5;
	tree.sources[0].content_manifest.total_bytes = 5;
	tree.manifest_digest = manifestDigestOf(tree);
	assert.throws(() => validateManifest(tree), /tree digest/);
});

test("W2929: content entries are bytewise sorted and unique", () => {
	const unsorted = validManifest();
	const content = unsorted.sources[0].content_manifest;
	content.entries = [
		{ path: "b.md", bytes: 2, content_digest: `sha256:${"1".repeat(64)}` },
		{ path: "a.md", bytes: 2, content_digest: `sha256:${"1".repeat(64)}` }];
	content.entry_count = 2;
	content.total_bytes = 4;
	content.tree_digest = digest(content.entries);
	unsorted.manifest_digest = manifestDigestOf(unsorted);
	assert.throws(() => validateManifest(unsorted), /sorted bytewise and unique/);

	// A DUPLICATE is the same refusal, and it must not slip through a
	// comparison that only asked for non-decreasing order.
	const duplicate = validManifest();
	const twice = duplicate.sources[0].content_manifest;
	twice.entries = [
		{ path: "a.md", bytes: 2, content_digest: `sha256:${"1".repeat(64)}` },
		{ path: "a.md", bytes: 2, content_digest: `sha256:${"1".repeat(64)}` }];
	twice.entry_count = 2;
	twice.total_bytes = 4;
	twice.tree_digest = digest(twice.entries);
	duplicate.manifest_digest = manifestDigestOf(duplicate);
	assert.throws(() => validateManifest(duplicate), /sorted bytewise and unique/);
});

test("W2929 review: content entry order is byte order, not UTF-16 order", () => {
	// UTF-8 byte order and JavaScript's UTF-16 relational comparison disagree
	// at the BMP/astral boundary. The frozen contract says BYTEWISE, and the
	// design model's Unicode ordering agrees with the UTF-8 bytes here.
	const document = validManifest();
	const content = document.sources[0].content_manifest;
	content.entries = [
		{ path: "\u{10000}.txt", bytes: 1,
		  content_digest: `sha256:${"1".repeat(64)}` },
		{ path: "\uE000.txt", bytes: 1,
		  content_digest: `sha256:${"2".repeat(64)}` },
	];
	assert.equal(content.entries[0].path < content.entries[1].path, true,
		"the fixture no longer exercises JavaScript's UTF-16 order");
	assert.equal(Buffer.compare(Buffer.from(content.entries[0].path),
	                           Buffer.from(content.entries[1].path)) > 0, true,
		"the fixture is no longer reversed under byte order");
	content.entry_count = 2;
	content.total_bytes = 2;
	content.tree_digest = digest(content.entries);
	document.manifest_digest = manifestDigestOf(document);
	assert.doesNotThrow(() =>
		validateSchemaFragment(structuredClone(document), "inputManifest",
			"input manifest"));
	assert.throws(() => validateManifest(document), /sorted bytewise and unique/);
});

test("W2929: a manifest digest recomputes with the member omitted", () => {
	// OMITTED, not nulled: a document with `manifest_digest: null` has
	// different canonical bytes and would seal to a different digest.
	const document = validManifest();
	assert.doesNotThrow(() => verifyManifestDigest(document));
	const { manifest_digest: _declared, ...rest } = document;
	assert.equal(document.manifest_digest, digest(rest));
	assert.notEqual(document.manifest_digest,
		digest({ ...rest, manifest_digest: null }));
	document.created_at = "2026-08-21T23:00:00.000Z";
	assert.throws(() => validateManifest(document), /digest does not recompute/);
});

test("W2929: a workspace destination cannot leave its workspace", () => {
	for (const bad of ["/absolute", "a/../b", "./a", "a//b", "a/", ""]) {
		assert.throws(() => validateRelativePath(bad, "destination"),
			(error) => error instanceof ContractError && error.code === "path",
			bad);
	}
	assert.doesNotThrow(() => validateRelativePath("workspace/source"));
});

test("W2929: input and output names are unique across both", () => {
	const document = validManifest();
	document.outputs[0].name = document.sources[0].name;
	document.manifest_digest = manifestDigestOf(document);
	assert.throws(() => validateManifest(document), /reuses an input\/output name/);
});

test("W2929: a git source's object format matches its base revision", () => {
	// §12 rule 7. A sha1 base under a sha256 repository is not a shorter
	// digest; it is a different object namespace.
	const document = validManifest();
	document.sources.push({
		name: "repo", type: "git", uri: "https://git.invalid/repo",
		destination: "workspace/repo", required: true,
		repository_id: "repo-1", object_format: "sha256",
		base_revision: { algorithm: "sha1", hex: "a".repeat(40) },
		source_ref: null, integration_ref: null,
		acquisition_policy_digest: `sha256:${"2".repeat(64)}`,
	});
	document.manifest_digest = manifestDigestOf(document);
	assert.throws(() => validateManifest(document), /base revision/);
});

test("W2929: a manifest carrying a secret is refused as a leak", () => {
	// §13 on the manifest boundary. Every descriptor in this document is a
	// closed object, so the leak has to arrive somewhere the schema
	// deliberately leaves open — the negotiated extensions bag is exactly
	// that, and it is exactly as durable as the rest of the manifest.
	const document = validManifest();
	document.extensions = {
		"x.vendor/1": { nested: { claim_token: GOLDEN_BEARER } } };
	document.manifest_digest = manifestDigestOf(document);
	assert.doesNotThrow(() =>
		validateSchemaFragment(structuredClone(document), "inputManifest",
			"input manifest"),
		"the schema now refuses this, so it no longer witnesses §13");
	assert.throws(() => validateManifest(document),
		(error) => error instanceof ContractError
			&& error.code === "secret-leak");
});


test("W2929: a URI outside the canonical grammar is refused", () => {
	// MIGRATED by the canonical-grammar ruling. This case used to assert that
	// OPAQUE forms stay accepted, on the reasoning that refusing a parse
	// failure "costs the contract nothing". The ruling supersedes that: the
	// worker-control 1.0 subset is deliberately hierarchical, so `urn:` and
	// `mailto:` are now refused and adding either back is a versioned contract
	// change rather than a parser exception. The malformed refusals are
	// retained unchanged.
	for (const bad of ["https://[", "https://a b", "http://:80", "://x",
	                   "urn:uuid:1", "mailto:worker@example.invalid"]) {
		assert.throws(() => validateUri(bad, "locator"),
			(error) => error instanceof ContractError, bad);
	}
	for (const good of ["artifact://inputs/source-1", "file:///srv/x",
	                    "https://source.invalid/archive"]) {
		assert.doesNotThrow(() => validateUri(good), good);
	}
	// An opaque form still answers to the original-text rules.
	assert.throws(() => validateUri("urn:uuid:1?x=1"), /query/);
	assert.throws(() => validateUri("mailto:a@b.invalid#f"), /fragment/);
});

test("W2929: a malformed locator cannot reach the trusted manifest", () => {
	const document = validManifest();
	document.sources[0].uri = "https://[";
	document.manifest_digest = manifestDigestOf(document);
	assert.doesNotThrow(() =>
		validateSchemaFragment(structuredClone(document), "inputManifest",
			"input manifest"),
		"the schema now refuses this, so it no longer witnesses rule 4");
	// MIGRATED: the grammar names the exact fault -- an unclosed bracket --
	// where the constructor could only say "not parseable".
	assert.throws(() => validateManifest(document), /does not close it/);
});

test("W2929: content entry order is UTF-8 byte order, not UTF-16", () => {
	// Round-4 review [P1]. `"\u{10000}"` starts with surrogate 0xD800 and
	// sorts BELOW `""` under JavaScript `<`; its UTF-8 bytes start
	// 0xF0 and sort ABOVE. The two orders disagree, and a seal both sides
	// of a cross-language boundary must reproduce cannot be built on the
	// one the contract does not name.
	const astral = "\u{10000}.txt";
	const bmp = ".txt";
	assert.ok(astral < bmp, "the fixture no longer separates the orders");
	assert.ok(Buffer.compare(Buffer.from(astral, "utf8"),
	                         Buffer.from(bmp, "utf8")) > 0,
		"the fixture no longer separates the orders");
	const seal = (entries) => ({
		entries,
		entry_count: entries.length,
		total_bytes: entries.reduce((sum, entry) => sum + entry.bytes, 0),
		tree_digest: digest(entries),
	});
	const entry = (path) => ({ path, bytes: 1,
	                           content_digest: `sha256:${"1".repeat(64)}` });
	// UTF-16 order: accepted before the correction, refused now.
	assert.throws(() => validateContentManifest(seal([entry(astral),
	                                                  entry(bmp)])),
		/sorted bytewise/);
	// BYTE order is the accepted one, and its aggregates and seal are exact.
	assert.doesNotThrow(() => validateContentManifest(seal([entry(bmp),
	                                                        entry(astral)])));
	// And through the whole trust entry, on a resealed manifest.
	const document = validManifest();
	document.sources[0].content_manifest = seal([entry(astral), entry(bmp)]);
	document.manifest_digest = manifestDigestOf(document);
	assert.throws(() => validateManifest(document), /sorted bytewise/);
});

test("W2929: a known bearer VALUE is refused whatever field carries it", () => {
	// Round-4 review [P1]. The walk screened field NAMES, which reads as a
	// leak boundary while being a naming convention.
	for (const durable of [
			{ diagnostic: GOLDEN_BEARER },
			{ message: `retention refused ${GOLDEN_BEARER}` },
			{ nested: [{ deep: { note: `x${GOLDEN_BEARER}y` } }] },
			[`${GOLDEN_BEARER}`],
			`${GOLDEN_BEARER}`,
			{ [`key-${GOLDEN_BEARER}`]: 1 }]) {
		assert.throws(() => assertNoDurableSecret(durable, "a durable result"),
			(error) => error instanceof ContractError
				&& error.code === "secret-leak",
			JSON.stringify(durable).slice(0, 60));
	}
	// The VERIFIER is not the secret — it is the whole point of having one,
	// and a check that refused it would make the durable record impossible.
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ verifier: GOLDEN_VERIFIER }, "an offer row"));
});

test("W2929: a registered secret is live until it is spent", () => {
	// The API the orchestration slice will use. Registration is by VALUE
	// because the question at a durable surface is only "is this the
	// secret", never "whose was it".
	const bearer = `${"q".repeat(40)}-live`;
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "before"));
	rememberSecret(bearer);
	try {
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "while"),
			(error) => error.code === "secret-leak");
	} finally {
		forgetSecret(bearer);
	}
	// Spent: the verifier is single-use, so the value it authenticated stops
	// being live at the same moment and the set does not grow without bound.
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "after"));
	// `withSecret` releases even when the act throws — a caller that failed
	// must not leave the value live.
	assert.throws(() => withSecret(bearer, () => { throw new Error("boom"); }),
		/boom/);
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "released"));
	// Shape alone is NOT the test: an ordinary durable operand of bearer
	// length is not a secret, and refusing it would refuse real manifests.
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ note: "z".repeat(43) }, "an ordinary operand"));
});

test("W2929 review: a nested secret scope cannot release its outer owner", () => {
	// A Set records presence, not lifetime ownership. The orchestration slice
	// may remember a live offer bearer and then scope one act with the same
	// value; releasing the inner act must not silently unregister the offer.
	const bearer = `${"n".repeat(40)}-nested`;
	rememberSecret(bearer);
	try {
		withSecret(bearer, () => {
			assert.throws(() => assertNoDurableSecret({ note: bearer }, "inner"),
				(error) => error.code === "secret-leak");
		});
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "outer"),
			(error) => error.code === "secret-leak",
			"the inner finally forgot the still-live outer registration");
	} finally {
		forgetSecret(bearer);
	}
});

test("W2929 review: a promise-returning secret scope stays live until settle", async () => {
	// `withSecret` is the API advertised to the not-yet-landed orchestration
	// slice. A provider act is naturally asynchronous; returning its Promise
	// is not completion and cannot release the bearer before the continuation.
	const bearer = `${"a".repeat(40)}-async`;
	let continueAct;
	const gate = new Promise((resolve) => { continueAct = resolve; });
	const act = withSecret(bearer, async () => {
		await gate;
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "continued"),
			(error) => error.code === "secret-leak");
	});
	assert.throws(() => assertNoDurableSecret({ note: bearer }, "pending"),
		(error) => error.code === "secret-leak",
		"returning a pending Promise released the secret immediately");
	continueAct();
	await act;
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "settled"));
});


test("W2929: secret registrations nest and the seed is never released", () => {
	// Round-5 review [P1]. A Set records presence; ownership needs a count.
	const bearer = `${"r".repeat(40)}-count`;
	rememberSecret(bearer);
	rememberSecret(bearer);
	forgetSecret(bearer);
	assert.throws(() => assertNoDurableSecret({ note: bearer }, "one owner left"),
		(error) => error.code === "secret-leak");
	forgetSecret(bearer);
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "released"));
	// An unbalanced release of a value nobody holds changes nothing rather
	// than going negative and swallowing the next registration — and it
	// reports the value GONE, because that is what the guard says. Round-8
	// review [P2]: this asserted `false` here, which contradicted the
	// agreement rule the very next case pins. The state transition is inert;
	// the liveness answer is not a report of what the call did.
	assert.equal(forgetSecret(bearer), true);
	rememberSecret(bearer);
	assert.throws(() => assertNoDurableSecret({ note: bearer }, "re-held"),
		(error) => error.code === "secret-leak");
	forgetSecret(bearer);

	// THE SEED IS PINNED. Nothing acquired the build's own golden bearer, so
	// nothing may hand it back — a scoped use of it, or a stray release, must
	// not leave the one value this build knows at rest writable to disk.
	withSecret(GOLDEN_BEARER, () => undefined);
	forgetSecret(GOLDEN_BEARER);
	forgetSecret(GOLDEN_BEARER);
	assert.throws(() => assertNoDurableSecret({ note: GOLDEN_BEARER }, "seed"),
		(error) => error.code === "secret-leak",
		"the pinned conformance bearer was released");
});

test("W2929 review: releasing a pinned registration never reports it gone", () => {
	// `forgetSecret`'s public result means the value is no longer live, and
	// its contract explicitly says a pinned value never is. Releasing one
	// dynamic registration of the golden bearer may remove that owner, but it
	// cannot report `true` while the build's pinned protection still holds.
	rememberSecret(GOLDEN_BEARER);
	assert.equal(forgetSecret(GOLDEN_BEARER), false,
		"a still-pinned secret was reported as gone");
	assert.throws(() =>
		assertNoDurableSecret({ note: GOLDEN_BEARER }, "still pinned"),
		(error) => error.code === "secret-leak");
});

test("W2929: an async scope holds until it settles, and rejects cleanly",
	async () => {
		// The reviewer's case covers a resolving act. A REJECTING one takes
		// the same path and must also release — a provider that failed is the
		// likeliest way to strand a registration forever.
		const bearer = `${"j".repeat(40)}-reject`;
		let fail;
		const gate = new Promise((_resolve, reject) => { fail = reject; });
		const act = withSecret(bearer, () => gate);
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "pending"),
			(error) => error.code === "secret-leak");
		fail(new Error("provider failed"));
		await assert.rejects(act, /provider failed/);
		assert.doesNotThrow(() =>
			assertNoDurableSecret({ note: bearer }, "settled"));
	});

test("W2929: an async scope nests with a live outer owner", async () => {
	// The two corrections meet here: the inner scope is asynchronous AND the
	// value is already owned. Neither the settle nor the outer release may
	// end the other's lifetime.
	const bearer = `${"m".repeat(40)}-both`;
	rememberSecret(bearer);
	try {
		await withSecret(bearer, async () => undefined);
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "outer"),
			(error) => error.code === "secret-leak",
			"the settling inner scope released the outer owner");
	} finally {
		forgetSecret(bearer);
	}
	assert.doesNotThrow(() => assertNoDurableSecret({ note: bearer }, "done"));
});

test("W2929 review: a thenable is inspected once and held until completion",
	async () => {
		// Reading `.then` to classify the result and asking `Promise.resolve` to
		// read it again is another time-of-check/time-of-use split. A stateful
		// thenable can expose its continuation once; consuming that read only as
		// a predicate makes the wrapper settle while the represented act is live.
		const bearer = `${"t".repeat(40)}-thenable`;
		let finish;
		const gate = new Promise((resolve) => { finish = resolve; });
		let reads = 0;
		const outcome = {};
		Object.defineProperty(outcome, "then", { get() {
			reads += 1;
			return reads === 1 ? gate.then.bind(gate) : undefined;
		} });
		let settled = false;
		const act = withSecret(bearer, () => outcome);
		act.then(() => { settled = true; });
		await new Promise((resolve) => setImmediate(resolve));
		let stayedLive = false;
		try {
			assertNoDurableSecret({ note: bearer }, "pending thenable");
		} catch (error) {
			stayedLive = error.code === "secret-leak";
		}
		const prematurelySettled = settled;
		finish();
		await act;
		assert.equal(reads, 1, "the thenable continuation was read twice");
		assert.equal(prematurelySettled, false,
			"the wrapper settled before the represented act completed");
		assert.equal(stayedLive, true,
			"the bearer was released while the represented act was live");
		assert.doesNotThrow(() =>
			assertNoDurableSecret({ note: bearer }, "settled thenable"));
	});


test("W2929: a throwing `then` getter releases synchronously", () => {
	// Round-6 review [P1] requires this explicitly. Classification now READS
	// the continuation rather than testing for it, so the read itself can
	// throw — and a value whose classification failed was never handed to
	// anyone, so nothing else will ever release it.
	const bearer = `${"g".repeat(40)}-getter`;
	const hostile = {};
	Object.defineProperty(hostile, "then", {
		get() { throw new Error("hostile getter"); },
	});
	assert.throws(() => withSecret(bearer, () => hostile), /hostile getter/);
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ note: bearer }, "after a failed read"),
		"a value whose classification threw stayed registered forever");
});

test("W2929: a thenable that rejects through its captured continuation "
	+ "releases", async () => {
		// The captured callable is used for BOTH settlements. A rejecting
		// thenable is the likeliest way a provider act ends badly, and it
		// must release exactly like a resolving one.
		const bearer = `${"h".repeat(40)}-thenable-reject`;
		let fail;
		const outcome = {
			then(resolve, reject) { fail = reject; },
		};
		const act = withSecret(bearer, () => outcome);
		assert.throws(() => assertNoDurableSecret({ note: bearer }, "pending"),
			(error) => error.code === "secret-leak");
		fail(new Error("the provider failed"));
		await assert.rejects(act, /the provider failed/);
		assert.doesNotThrow(() =>
			assertNoDurableSecret({ note: bearer }, "settled"));
	});

test("W2929: a non-callable `then` is an ordinary value, not an act", () => {
	// The classification is `typeof continuation === "function"`, so a plain
	// object carrying a `then` STRING is data and releases synchronously.
	// Treating it as asynchronous would strand the bearer forever, since
	// nothing would ever call it back.
	const bearer = `${"k".repeat(40)}-not-thenable`;
	const outcome = withSecret(bearer, () => ({ then: "not a function" }));
	assert.deepEqual(outcome, { then: "not a function" });
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ note: bearer }, "released"));
});

test("W2929: the release answer agrees with the guard, in both directions", () => {
	// Round-7 review [P2]. The boolean is a statement about liveness, so the
	// property is AGREEMENT: whatever `forgetSecret` reports, the guard must
	// behave that way. A `true` that the guard contradicts sends future
	// orchestration to the wrong conclusion even when nothing leaks.
	const live = (value) => {
		try {
			assertNoDurableSecret({ note: value }, "probe");
			return false;
		} catch (error) {
			assert.equal(error.code, "secret-leak");
			return true;
		}
	};
	// An ORDINARY value: nested owners, then gone — and the guard agrees at
	// every step, so the pinned case is not the only thing this asserts.
	const bearer = `${"y".repeat(40)}-agree`;
	rememberSecret(bearer);
	rememberSecret(bearer);
	assert.equal(forgetSecret(bearer), false);
	assert.equal(live(bearer), true);
	assert.equal(forgetSecret(bearer), true);
	assert.equal(live(bearer), false);
	// AND RELEASING IT AGAIN. Round-8 review [P2]: my first version of this
	// case stopped at the last owner, so the `no dynamic owner` branch was
	// never asked — and it answered "still live" for a value the guard had
	// already let through. An agreement case that never exercises every
	// branch is agreement about the branches it happened to visit.
	assert.equal(forgetSecret(bearer), true)
	assert.equal(live(bearer), false)
	// A PINNED value: every release reports still-live, because it is.
	rememberSecret(GOLDEN_BEARER);
	assert.equal(forgetSecret(GOLDEN_BEARER), false);
	assert.equal(live(GOLDEN_BEARER), true);
	// Including an unbalanced one, which finds no dynamic owner at all.
	assert.equal(forgetSecret(GOLDEN_BEARER), false);
	assert.equal(live(GOLDEN_BEARER), true);
	// And the scoped form, whose release runs the same path.
	withSecret(GOLDEN_BEARER, () => undefined);
	assert.equal(live(GOLDEN_BEARER), true);
});

test("W2929 review: an already-gone ordinary secret still reports gone", () => {
	// Round 8 pins the boolean as a description of the guard's CURRENT
	// liveness, not as a report that this particular call found an owner.
	// An unbalanced release is state-inert, but after the last ordinary owner
	// has released the value is still gone and the guard says so. Returning
	// false here contradicts the same agreement rule the pinned correction
	// applies to GOLDEN_BEARER in the other direction.
	const bearer = `${"u".repeat(40)}-already-gone`;
	rememberSecret(bearer);
	assert.equal(forgetSecret(bearer), true);
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ note: bearer }, "after the last owner"));
	assert.equal(forgetSecret(bearer), true,
		"an already-gone ordinary value was reported still live");
	assert.doesNotThrow(() =>
		assertNoDurableSecret({ note: bearer }, "after an inert release"));
});


test("the shared locator vectors are the authority for both runtimes", () => {
	// ONE LIST, TWO IMPLEMENTATIONS. The ruling makes
	// `fixtures/uri-vectors.json` the authority for this grammar rather than
	// two implementations that agree today; the Python contracts package reads
	// the same file and runs the same assertions.
	const vectors = JSON.parse(readFileSync(
		join(dirname(fileURLToPath(import.meta.url)), "..", "fixtures",
		     "uri-vectors.json"), "utf8"));
	assert.ok(vectors.accepted.length >= 15);
	assert.ok(vectors.refused.length >= 40);
	for (const uri of vectors.accepted) {
		assert.doesNotThrow(() => validateUri(uri, "locator"), uri);
	}
	for (const { uri, why } of vectors.refused) {
		assert.throws(() => validateUri(uri, "locator"),
			(error) => error instanceof ContractError, `${uri} (${why})`);
	}
});

test("no locator names an address the two runtimes spell differently", () => {
	// The IPv4-MAPPED family, `::ffff:0:0/96`, is excluded from the shared
	// grammar. Not a rule about addresses -- a rule about AGREEMENT: this
	// constructor's canonical text for the family is the hex form and Python's
	// `ipaddress` writes the dotted form, so each refuses the other's spelling
	// and there is no mapped locator both runtimes can read. The measurement
	// is asserted here rather than described, so a future runtime that spells
	// it the other way fails this case instead of silently changing what a
	// durable locator means.
	assert.equal(new URL("http://[::ffff:1.2.3.4]").hostname,
		"[::ffff:102:304]");
	// The dotted spelling never reaches this rule: the literal alphabet has
	// already refused it, which is the same answer for a nearer reason.
	assert.throws(() => validateUri("https://[::ffff:1.2.3.4]/x", "locator"),
		(error) => error instanceof ContractError);
	for (const literal of ["::ffff:102:304", "::ffff:0:0", "::ffff:0:1"]) {
		assert.throws(() => validateUri(`https://[${literal}]/x`, "locator"),
			(error) => error instanceof ContractError
				&& /IPv4-mapped/.test(error.message), literal);
	}
	// The exclusion is the mapped range and not everything shaped like it:
	// `::ffff:1` is `0:0:0:0:0:0:ffff:1`, an ordinary address both runtimes
	// spell the same way.
	assert.doesNotThrow(() => validateUri("https://[::ffff:1]/x", "locator"));
});

test("a DNS name is held to the DNS bounds", () => {
	// The character rules were here and the LENGTH rules were not, so a
	// 64-byte label -- a name no resolver will ever carry -- was a durable
	// locator as far as this contract was concerned.
	const label = "a".repeat(63);
	assert.doesNotThrow(() => validateUri(`https://${label}.test/x`));
	const longest = [label, label, label, "a".repeat(61)].join(".");
	assert.equal(longest.length, 253);
	assert.doesNotThrow(() => validateUri(`https://${longest}/x`));
	for (const host of ["a".repeat(64), `ok.${"a".repeat(64)}.test`,
	                    [label, label, label, label].join("."),
	                    [label, label, label, "a".repeat(62)].join(".")]) {
		assert.throws(() => validateUri(`https://${host}/x`, "locator"),
			(error) => error instanceof ContractError, host);
	}
});

test("the literal alphabet guards an assumption about this runtime", () => {
	// The alphabet clause in `validateUriIpv6` currently refuses nothing this
	// constructor would have accepted -- measured, and a mutation deleting the
	// clause survives. It is kept anyway because it is the only clause there
	// that does not ask a third-party normalizer, and this case pins the
	// assumption that makes it look redundant. If a future runtime starts
	// accepting a scope id or a dotted quad and returning it unchanged, this
	// fails HERE, pointing at the clause that is holding the grammar still,
	// rather than silently widening what a durable locator may say.
	for (const outside of ["fe80::1%eth0", "fe80::1%25eth0", "::%1"]) {
		let hostname = null;
		try { hostname = new URL(`http://[${outside}]`).hostname; } catch {}
		assert.notEqual(hostname, `[${outside}]`,
			`this runtime now round-trips ${outside}; the alphabet clause in `
			+ `validateUriIpv6 is what keeps the grammar fixed`);
	}
	// The dotted quad is accepted by the constructor and REWRITTEN, which is
	// the same divergence from the other direction.
	assert.equal(new URL("http://[::ffff:1.2.3.4]").hostname,
		"[::ffff:102:304]");
});
