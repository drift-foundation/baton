// W2929: THE RETAINED MANIFESTS.
//
// Review [P1] on the freeze slice, twice over. A digest is not a record: the
// store held `attempt.input_digest` and `outputs.manifest_digest` and not one
// byte of either document, so
//
//   - freeze could not compare the sealed result against the OUTPUT
//     DECLARATIONS the input manifest names, because it never saw them; and
//   - intake, proposal publication and any restart were left with a number
//     and nothing to replay or inspect.
//
// One table serves both, because both are the same fact: a validated document
// this manager is holding, keyed by the digest that identifies it.
//
// THE KEY IS THE DIGEST, so retention is idempotent by construction — the
// same document stored twice is the same row. It is also why a stored body
// can never drift from its key: the key is computed from the bytes.

import { canonicalBytes, ContractError, digest, validateManifest }
	from "./contracts.mjs";

/** Validate a manifest and retain its canonical bytes.
 *
 *  Returns the digest that identifies it, which is what every other table
 *  stores. The document is validated FIRST — a manifest this manager could
 *  not read is not one it should be holding, and retaining it would make the
 *  store the place a malformed document survives. */
export function retainManifest(store, document, definition = "inputManifest",
                               what = "manifest") {
	const owned = validateManifest(document, definition, what);
	const { manifest_digest: _declared, ...rest } = owned;
	const key = digest(rest);
	const retained = retainCanonical(store.db, store.clock(), key, owned.schema,
	                                 canonicalBytes(owned).toString("utf8"));
	return { digest: key, manifest: owned, retained };
}

/** Compare-before-reference, on whatever handle is doing the writing.
 *
 *  Review [P1]: the result path wrote `INSERT OR IGNORE` and so BYPASSED the
 *  collision refusal this module exists to make. If the digest already named
 *  different bytes the insert was ignored, the `outputs` row committed a
 *  foreign key to those wrong bytes, and the operation reported the requested
 *  result as frozen while a reload returned a document its digest does not
 *  identify. One rule, one place, and every writer goes through it. */
export function retainCanonical(db, at, key, schema, bytes) {
	const found = db.prepare(
		"SELECT body FROM manifests WHERE digest = ?").get(key);
	if (found !== undefined) {
		// A digest collision with different bytes is not something SHA-256
		// hands out, but "cannot happen" is not a reason to write the second
		// one over the first — and the same check catches a store somebody
		// edited by hand.
		if (found.body !== bytes) {
			throw new ContractError("integrity", "digest",
				`${key} is already retained with different bytes; a digest `
				+ `identifies a document and cannot name two`);
		}
		return false;
	}
	db.prepare(
		"INSERT INTO manifests (digest, schema, body, retained_at) "
		+ "VALUES (?, ?, ?, ?)")
		.run(key, schema, bytes, at);
	return true;
}

/** The retained document for a digest, or null — VALIDATED AS WHAT THE CALLER
 *  ASKED FOR, and re-bound to its key.
 *
 *  Review [P1]: this parsed the row and handed it back. Nothing checked that
 *  the body was the KIND the caller needed, so a retained RESULT manifest —
 *  a perfectly valid thing to retain — could be named as an attempt's input
 *  digest and its similarly shaped output rows read as trusted DECLARATIONS.
 *  Being at the named key is not the same as being the named thing.
 *
 *  So the definition is REQUIRED rather than defaulted: a caller that has not
 *  said what it expects has not made the check that matters, and a default
 *  would let a new call site inherit somebody else's expectation silently.
 *
 *  And the digest is recomputed against the key, because a store nobody
 *  validates on the way out is a store where a hand edit outlives every
 *  guard on the way in.
 *
 *  Parsed fresh on every call. A cached object handed to two callers is a
 *  durable record one of them can edit for the other — the same
 *  time-of-check aliasing `validateManifest` already refuses to hand out. */
export function loadManifest(store, key, definition,
                             what = "retained manifest") {
	if (typeof definition !== "string" || definition.length === 0) {
		throw new ContractError("integrity", "schema",
			"loading a retained manifest names the kind it must be; a caller "
			+ "that does not say what it expects has not checked anything");
	}
	const found = store.db.prepare(
		"SELECT body FROM manifests WHERE digest = ?").get(key);
	if (found === undefined) return null;
	const owned = validateManifest(JSON.parse(found.body), definition, what);
	const { manifest_digest: _declared, ...rest } = owned;
	if (digest(rest) !== key) {
		throw new ContractError("integrity", "digest",
			`${what} is stored under ${key} and its bytes recompute to `
			+ `${digest(rest)}; a digest identifies the document it names`);
	}
	return owned;
}
