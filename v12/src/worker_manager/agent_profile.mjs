// W2929 plan item 4, first slice: CERTIFYING ONE AGENT-SESSION PROFILE.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance is one sentence and the ORDER inside it is the
// content:
//
//   "The core certifies one exact profile by composing shape, document seal
//    and policy checks IN THAT ORDER."
//
// SHAPE FIRST, because every later rule reads members, and reading a member
// the schema has not established is how the worker-control entry's round-2
// bypass happened. SEAL SECOND, because a policy decision about a document
// whose bytes do not match its own digest is a decision about something
// nobody agreed to. POLICY LAST, and only the rules the schema CANNOT state.
//
// `schema/agent-session-1.0.schema.json` is the frozen agent-session 1.0
// schema from
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-worker-contract/findings/finding-acp-agent-boundary/schema/`,
// placed here for the same reason the worker-control schema is: a manager
// that read a schema from another Work's dossier at run time would be
// certifying against a document somebody else may edit.
//
// WHAT IS NOT HERE: opening sessions, turns, event normalization and the
// adapter CONTRACTS — the rest of item 4. This slice answers one question,
// which is whether a profile may be certified at all.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { assertNoDurableSecret, canonicalBytes, ContractError, digest }
	from "./contracts.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
export const AGENT_SESSION_SCHEMA_PATH =
	join(HERE, "schema", "agent-session-1.0.schema.json");
export const AGENT_SESSION_SCHEMA =
	JSON.parse(readFileSync(AGENT_SESSION_SCHEMA_PATH).toString("utf8"));

// Its own compiler, with the same two settings and for the same two reasons
// the worker-control one carries: `strict: false` because the frozen schema
// is what it is, and format assertions OFF because turning the weaker check
// on would suggest a stronger one had run.
const _ajv = new Ajv2020({ strict: false, validateFormats: false,
                           allErrors: false });
const _validateProfile = _ajv.compile({
	...AGENT_SESSION_SCHEMA, $ref: "#/$defs/sessionProfile",
	oneOf: undefined,
});

/** Certify one exact agent-session profile: shape, seal, policy, in order.
 *
 *  Returns the sealed digest, which is what everything else stores. The
 *  document is certified BY DIGEST, because "the profile we agreed on" is a
 *  byte identity — a later edit to a file of the same name would otherwise
 *  recertify itself. */
export function certifyAgentSessionProfile(store, document,
                                           what = "agent-session profile") {
	// 1. SHAPE.
	const owned = structuredClone(document);
	if (!_validateProfile(owned)) {
		const first = _validateProfile.errors?.[0];
		throw new ContractError("integrity", "schema",
			`${what} is not a valid baton.agent-session 1.0 profile: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	// 2. THE DOCUMENT SEAL, over the document with `document_digest` OMITTED
	// — not nulled, not emptied, which are different documents with different
	// canonical bytes.
	const { document_digest: declared, ...rest } = owned;
	const sealed = digest(rest);
	if (declared !== sealed) {
		throw new ContractError("integrity", "digest",
			`${what} declares document digest ${declared} and its canonical `
			+ `bytes with that member omitted recompute to ${sealed}`);
	}
	// A profile is a durable document like any other.
	assertNoDurableSecret(owned, what);
	// 3. POLICY — only what the schema cannot state.
	//
	// THE TWO POSTURES CARRY DIFFERENT PINNED POLICIES, and a profile in
	// which they are equal is refused AT CERTIFICATION rather than at run
	// time. The schema pins consent to no workspace and no declared output,
	// which it can say because those are constants; it cannot compare two of
	// its own members, and a consent posture whose policy equals the
	// execution one is a consent session with execution's permissions — the
	// separation the two postures exist for, removed by a document that
	// otherwise validates.
	const consent = digest(owned.postures.consent.policy);
	const execution = digest(owned.postures.execution.policy);
	if (consent === execution) {
		throw new ContractError("policy", "profile-uncertified",
			`${what} pins the same policy for both postures; consent and `
			+ `execution differ or there is no separation to enforce`);
	}
	// THE BYTES, not just the digest. A session must pin the per-posture
	// policy this profile carries, and a digest cannot be read for it — the
	// same lesson the freeze review taught about results, applied before it
	// could be found again.
	const bytes = canonicalBytes(owned).toString("utf8");
	store.db.prepare(
		"INSERT INTO profiles (kind, name, digest, body, certified_at) "
		+ "VALUES ('agent-session', ?, ?, ?, ?) ON CONFLICT(kind, name) "
		+ "DO UPDATE SET digest = excluded.digest, body = excluded.body, "
		+ "certified_at = excluded.certified_at, withdrawn_at = NULL")
		.run(owned.profile_id, sealed, bytes, store.clock());
	return { profileId: owned.profile_id, digest: sealed, bytes };
}

/** The certified profile DOCUMENT for a digest, or null — re-validated and
 *  re-bound to the key it is filed under.
 *
 *  The loader lesson from the retained manifests, applied here rather than
 *  waited for: a row at the named key is not proof of what is in it, and a
 *  guard on the way IN cannot see an edit made afterwards. */
export function certifiedAgentSessionProfile(store, profileDigest) {
	const row = store.db.prepare(
		"SELECT body FROM profiles WHERE kind = 'agent-session' "
		+ "AND digest = ? AND withdrawn_at IS NULL").get(profileDigest);
	if (row === undefined || row.body === null) return null;
	const owned = JSON.parse(row.body);
	if (!_validateProfile(owned)) {
		throw new ContractError("integrity", "schema",
			`the retained profile under ${profileDigest} is not a valid `
			+ `baton.agent-session 1.0 profile`);
	}
	// ONE EQUALITY AMONG ALL THREE WITNESSES: what the document DECLARES,
	// what its canonical bytes RECOMPUTE to, and the KEY it is filed under.
	//
	// Review [P1]: the declared member was destructured away and never
	// compared, so a retained profile whose every other byte matched its key
	// could carry somebody else's well-formed seal and still open a session.
	// Two of three agreeing is not agreement.
	const { document_digest: declared, ...rest } = owned;
	const recomputed = digest(rest);
	if (recomputed !== profileDigest || declared !== profileDigest) {
		throw new ContractError("integrity", "digest",
			`the profile retained under ${profileDigest} declares ${declared} `
			+ `and recomputes to ${recomputed}; a digest, the document that `
			+ `declares it and the key it is filed under are one fact`);
	}
	return owned;
}

/** Whether THIS digest names a currently certified agent-session profile.
 *
 *  A withdrawn profile is not certified — that is what withdrawal means — so
 *  the row answers only while `withdrawn_at` is null. */
export function isAgentSessionProfileCertified(store, profileDigest) {
	const row = store.db.prepare(
		"SELECT digest FROM profiles WHERE kind = 'agent-session' "
		+ "AND digest = ? AND withdrawn_at IS NULL").get(profileDigest);
	return row !== undefined;
}
