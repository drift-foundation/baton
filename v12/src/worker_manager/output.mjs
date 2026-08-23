// W2929 plan item 3, fourth slice: THE OUTPUT FREEZE.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance, in one sentence: "Freeze requires the exact live
// assignment, terminal agent-turn handling compatible with the declared
// disposition, and a positive writer-quiescence observation. The same digest
// replays; changed bytes under the same identity refuse. W2930 owns
// filesystem/OCI collection, while W2929 owns the immutable store transition
// and validation of the adapter's sealed observation."
//
// So this slice is the STORE TRANSITION and the VALIDATION, and nothing about
// how bytes are gathered.
//
// THE FOUR PRECONDITIONS, and where each is actually decided:
//
//   1. the attempt carries a fixed four-part assignment            — the row
//   2. the session is bound to that participant                    — the API
//   3. `worker_disposition` is already TERMINAL and equals the one
//      being declared                                              — the row
//   4. `execution_runtime` is positively `quiescent`               — the row
//
// and then the assignment must still be LIVE at the authority, which is a
// READ of somebody else's store and can only ever be a read. That is stated
// rather than hidden: see `requestFreeze`.
//
// WHAT IS NOT HERE: intake and cleanup, and all of item 4. In particular the
// agent TURN records that gate the disposition are item 4's (store surface
// item 8) — which is why this slice compares against the recorded
// `worker_disposition` axis rather than accepting a turn outcome from its
// caller. A proof the caller can write is not a proof.

import { canonicalBytes, ContractError, digest, validateManifest }
	from "./contracts.mjs";
import { observe } from "./attempts.mjs";
import { loadManifest, retainCanonical } from "./manifests.mjs";

const ASSIGNMENT_FIELDS =
	Object.freeze(["authorityUuid", "workId", "participant", "generation"]);

function attemptOf(store, attemptId) {
	const row = store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id = ?").get(attemptId);
	if (row === undefined) {
		throw new ContractError("refused", "precondition",
			`no runtime attempt ${attemptId}`);
	}
	return row;
}

function fixedAssignment(attempt) {
	if (attempt.assignment_generation === null) return null;
	return { authorityUuid: attempt.authority_uuid, workId: attempt.work_id,
	         participant: attempt.assignment_participant,
	         generation: attempt.assignment_generation };
}

function sameAssignment(left, right) {
	return ASSIGNMENT_FIELDS.every((field) => left?.[field] === right?.[field]);
}

/** The ONE fixed freeze operation for an attempt's exact generation.
 *
 *  Derived, like every other act in this manager, so a restart names what it
 *  already did rather than sealing a second time. */
export function freezeOperationId(attempt) {
	return `output.freeze:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
	}).slice("sha256:".length)}`;
}

/** THE WHOLE freeze operation identity: the id AND its signature.
 *
 *  Review [P1]: only the id reached the adapter and only the id was compared
 *  when the result came back, so any schema-shaped digest was accepted in
 *  `freeze_operation.signature_digest` — and the original fixture supplied
 *  one unrelated to the journalled operation while every case stayed green.
 *  THE ID IS THE RETRY KEY; THE SIGNATURE IS THE BINDING over the kind and
 *  every effective operand. Comparing the key alone compares the weaker half.
 *
 *  The disposition is read from the attempt rather than taken as an operand,
 *  because by the time this is derived the freeze has already proved the
 *  declared one equals the recorded axis. */
export function freezeOperation(attempt) {
	const operationId = freezeOperationId(attempt);
	return {
		operation_id: operationId,
		signature_digest: digest({ kind: "output.freeze", operands: {
			attemptId: attempt.runtime_attempt_id,
			expect: fixedAssignment(attempt),
			disposition: attempt.worker_disposition,
			operationId } }),
	};
}

/** The record operation is FIXED PER ATTEMPT, not per digest.
 *
 *  This is the whole mechanism behind "the same digest replays; changed bytes
 *  under the same identity refuse". If the identity varied with the bytes,
 *  two different results would be two different operations and BOTH would
 *  commit — which is the opposite of what an immutable record means. The
 *  identity is the act; the signature carries the bytes. */
export function recordOperationId(attempt) {
	return `output.record:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
	}).slice("sha256:".length)}`;
}

/** Step 1: request the freeze, then hand the adapter the act it is settling.
 *
 *  Every precondition below is read from DURABLE state. None of them is a
 *  claim the caller supplied about itself. */
export function requestFreeze(store, session, adapter,
                              { attemptId, disposition }) {
	if (typeof adapter?.seal !== "function") {
		throw new ContractError("integrity", "schema",
			"the runtime adapter must supply seal(); the freeze transition "
			+ "exists to record what a seal produced");
	}
	const attempt = attemptOf(store, attemptId);
	const expect = fixedAssignment(attempt);
	if (expect === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} has no fixed assignment; a result belongs `
			+ `to an exact generation and there is none`);
	}
	if (session.participant !== expect.participant) {
		throw new ContractError("refused", "capability",
			`this session acts for ${session.participant} and attempt `
			+ `${attemptId} is assigned to ${expect.participant}`);
	}
	// POSITIVE QUIESCENCE, and nothing weaker.
	//
	// A seal describes a tree that has stopped changing. `uncertain` is not
	// quiescence — it is a failure to look — and `destroyed` is not either:
	// a writer that is gone was never observed to have finished. The pinned
	// refusal code for this exact question is `quiescence-unknown`, and it
	// says what is missing rather than blaming the caller's request.
	if (attempt.execution_runtime !== "quiescent") {
		throw new ContractError("runtime-observation", "quiescence-unknown",
			`attempt ${attemptId} execution is ${attempt.execution_runtime}; `
			+ `a freeze describes a tree the writer has stopped changing, and `
			+ `only a positive quiescent observation says that`);
	}
	// THE DISPOSITION IS COMPARED, NOT ACCEPTED.
	//
	// The turn outcome gates the disposition and never chooses it, and turn
	// records are item 4's. What item 3 can decide is that a terminal
	// disposition was RECORDED before the freeze and that the freeze declares
	// that same one — which is a comparison against durable state rather than
	// a caller's assertion about a turn nobody here can see.
	if (attempt.worker_disposition === "none") {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} has no recorded worker disposition; the `
			+ `handled turn outcome gates it and none has been observed`);
	}
	if (attempt.worker_disposition !== disposition) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} recorded disposition `
			+ `${attempt.worker_disposition} and this freeze declares `
			+ `${disposition}`);
	}
	const operation = freezeOperation(attempt);
	const operationId = operation.operation_id;
	store.transact(operationId, "output.freeze",
		operation.signature_digest, () => {
		// THE LIVENESS READ IS INSIDE THE WRITE, and it is still only a read.
		//
		// The authority is a different store, so nothing this manager does
		// can make "still live" and "recorded frozen" one atomic fact. The
		// window is made as small as it can be — and the design does not
		// depend on it being zero: material from an assignment that ended
		// anyway is quarantined at INTAKE rather than trusted here. That is
		// why this is a precondition and not a proof.
		const live = session.assignmentOf(expect.workId);
		if (live === null) {
			throw new ContractError("stale-assignment", "ended",
				`${expect.workId} holds no live assignment; a result is never `
				+ `published on a dead generation`);
		}
		if (!sameAssignment(live, expect)) {
			throw new ContractError("stale-assignment", "generation",
				`the live assignment is ${JSON.stringify(live)} and this `
				+ `attempt is fixed to ${JSON.stringify(expect)}`);
		}
		observe(store, { attemptId, axis: "output", value: "freeze-requested" });
		return { attemptId, operationId, disposition };
	});
	// THE WHOLE IDENTITY crosses the boundary. An adapter handed only the
	// retry key cannot echo the binding, and a manager that asks for an echo
	// it never supplied is asking the adapter to guess.
	const sealed = adapter.seal({ attemptId, assignment: expect, disposition,
	                              operation });
	return recordFrozenResult(store, { attemptId, sealed });
}

/** Step 2: validate the adapter's sealed observation and record it, once.
 *
 *  `validateManifest` already carries the portable rules — schema, the
 *  manifest digest recomputed over its own canonical bytes, no durable
 *  secret, well-formed refs, and every content manifest's sorted-unique
 *  paths, counts, byte totals and tree digest. What it CANNOT know is
 *  whether this document belongs to THIS attempt, and that is the whole of
 *  what is added below. */
export function recordFrozenResult(store, { attemptId, sealed }) {
	const attempt = attemptOf(store, attemptId);
	const expect = fixedAssignment(attempt);
	const owned = validateManifest(sealed, "resultManifest",
	                               `attempt ${attemptId} sealed result`);
	// THE IMMUTABLE IDENTITY FIRST, before anything about today.
	//
	// Recomputed rather than copied. This is NOT an extra guard and is not
	// counted as one: `validateManifest` above already refused any document
	// whose declared digest does not recompute, so the two values are equal
	// by then and a mutation swapping them is equivalent. What it buys is
	// provenance — the number stored beside the result is derived from the
	// bytes rather than lifted from a field the document filled in about
	// itself, so a later reader of this row is reading a computation.
	const { manifest_digest: _declared, ...rest } = owned;
	const recomputed = digest(rest);
	const operationId = recordOperationId(attempt);
	const signature = digest({ kind: "output.record",
	                           operands: { attemptId, recomputed } });
	// Review [P1], twice. First the output axis was consulted ahead of the
	// journal, so an exact retry refused once `output` reached `sealed`. Then
	// the correction left the DECLARATION lookup ahead of it, so removing an
	// old input row made an exact retry refuse too. Replay is a fact about an
	// identity that already settled; NOTHING about today is a precondition
	// for reproducing the answer it produced. Every check below this line
	// applies to a genuinely new record.
	const already = store.replay(operationId, signature);
	if (already.found) return already.value;
	const bound = {
		authorityUuid: owned.assignment_ref.work_ref.authority_uuid,
		workId: owned.assignment_ref.work_ref.work_id,
		participant: owned.assignment_ref.participant,
		generation: owned.assignment_ref.generation,
	};
	if (!sameAssignment(bound, expect)) {
		throw new ContractError("stale-assignment", "target",
			`the sealed result names ${JSON.stringify(bound)} and this `
			+ `attempt is fixed to ${JSON.stringify(expect)}`);
	}
	// The pinned digests, compared rather than trusted. A result that named
	// a different input or policy would be a result for a different job
	// wearing this assignment's reference.
	for (const [field, stored, seen] of [
			["input", attempt.input_digest, owned.input_manifest_digest],
			["policy", attempt.policy_digest, owned.policy_digest]]) {
		if (stored !== seen) {
			throw new ContractError("integrity", "digest",
				`the sealed result declares ${field} digest ${seen} and this `
				+ `attempt was recorded with ${stored}`);
		}
	}
	if (owned.disposition !== attempt.worker_disposition) {
		throw new ContractError("refused", "precondition",
			`the sealed result declares ${owned.disposition} and this `
			+ `attempt recorded ${attempt.worker_disposition}`);
	}
	const operation = freezeOperation(attempt);
	if (owned.freeze_operation.operation_id !== operation.operation_id) {
		throw new ContractError("refused", "precondition",
			`the sealed result settles ${owned.freeze_operation.operation_id} `
			+ `and this attempt's freeze is ${operation.operation_id}`);
	}
	// AND THE SIGNATURE, which is the half that binds. Review [P1]: only the
	// id was compared, so a result echoing the right retry key with any
	// schema-shaped digest was accepted as settling this freeze.
	if (owned.freeze_operation.signature_digest !== operation.signature_digest) {
		throw new ContractError("integrity", "digest",
			`the sealed result echoes freeze signature `
			+ `${owned.freeze_operation.signature_digest} and this attempt's `
			+ `freeze was journalled under ${operation.signature_digest}`);
	}
	// THE DECLARED OUTPUTS, against the declaration this attempt names.
	//
	// Review [P1]: the store held only `input_digest`, so a schema-valid
	// result could substitute an undeclared output or drop a required one
	// while echoing the expected digest. `validateManifest` can prove a
	// document is internally well formed; it cannot compare it with a
	// document it never sees.
	const declaration = loadManifest(store, attempt.input_digest,
		"inputManifest", `attempt ${attemptId} input declaration`);
	if (declaration === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} names input manifest ${attempt.input_digest} `
			+ `and this manager does not hold it; declared outputs cannot be `
			+ `compared against a document nobody retained`);
	}
	compareDeclaredOutputs(declaration, owned, attemptId);
	if (attempt.output !== "freeze-requested") {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} output is ${attempt.output}; a result is `
			+ `recorded against a requested freeze`);
	}
	return store.transact(operationId, "output.record", signature, (db) => {
		// THE SEALED OBSERVATION IS RETAINED, not summarized.
		//
		// Review [P1]: a summary row and the artifact references were all
		// that survived — every content tree, every explicitly missing
		// output, the evidence and the freeze operation disappeared when the
		// call returned, leaving intake, publication and restart with a
		// digest and nothing to replay. The canonical bytes are stored under
		// the digest that identifies them, so what comes back out is what
		// went in.
		retainCanonical(db, store.clock(), recomputed, owned.schema,
		                canonicalBytes(owned).toString("utf8"));
		db.prepare(
			"INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
			+ "manifest_digest, freeze_operation_id, frozen_at) "
			+ "VALUES (?, ?, ?, ?, ?, ?)")
			.run(attemptId, owned.result_id, owned.disposition, recomputed,
			     operation.operation_id, store.clock());
		for (const output of owned.outputs) {
			if (output.artifact === null) continue;
			db.prepare(
				"INSERT INTO output_artifacts (runtime_attempt_id, "
				+ "output_name, artifact_id, media_type, bytes, "
				+ "content_digest, locator) VALUES (?, ?, ?, ?, ?, ?, ?)")
				.run(attemptId, output.name, output.artifact.artifact_id,
				     output.artifact.media_type, output.artifact.bytes,
				     output.artifact.content_digest, output.artifact.locator);
		}
		observe(store, { attemptId, axis: "output", value: "frozen" });
		return { attemptId, resultId: owned.result_id,
		         manifestDigest: recomputed, disposition: owned.disposition };
	});
}

/** The result's outputs, against the input manifest's DECLARATIONS.
 *
 *  The pinned rule, from the umbrella finding: "A Job may declare several
 *  outputs; an undeclared path is never collected merely because the agent
 *  wrote there," and "Missing or invalid required output prevents a
 *  successful result; an inability disposition may return evidence without
 *  pretending the requested result exists."
 *
 *  So the comparison runs BOTH WAYS. Every result output must be declared,
 *  and every declaration must be answered — a declaration silently dropped
 *  from the result is not an answer to it, it is a question the result
 *  pretends was never asked. */
function compareDeclaredOutputs(declaration, result, attemptId) {
	const declared = new Map(
		declaration.outputs.map((output) => [output.name, output]));
	const answered = new Map();
	for (const output of result.outputs) {
		if (answered.has(output.name)) {
			throw new ContractError("integrity", "schema",
				`the sealed result answers output ${output.name} twice; two `
				+ `answers to one declaration is not an answer`);
		}
		answered.set(output.name, output);
		const expect = declared.get(output.name);
		if (expect === undefined) {
			throw new ContractError("integrity", "schema",
				`the sealed result carries output ${output.name}, which the `
				+ `input manifest does not declare; an undeclared path is `
				+ `never collected merely because the agent wrote there`);
		}
		if (expect.type !== output.type) {
			throw new ContractError("integrity", "schema",
				`output ${output.name} is declared ${expect.type} and the `
				+ `sealed result reports ${output.type}`);
		}
	}
	for (const [name, expect] of declared) {
		const seen = answered.get(name);
		if (seen === undefined) {
			throw new ContractError("integrity", "schema",
				`the input manifest declares output ${name} and the sealed `
				+ `result does not answer it`);
		}
		// A REQUIRED OUTPUT THAT IS NOT THERE IS NOT A COMPLETION. An
		// inability disposition may return evidence without pretending the
		// requested result exists, which is exactly why this is conditioned
		// on the disposition rather than refused outright.
		checkDeclaredLimits(name, expect, seen);
		if (expect.required && seen.status !== "present"
				&& result.disposition === "completed") {
			throw new ContractError("integrity", "schema",
				`attempt ${attemptId} declares output ${name} required and `
				+ `the sealed result reports ${seen.status} under a completed `
				+ `disposition`);
		}
	}
}

/** The declared LIMITS, against what the sealed observation already proves.
 *
 *  Review [P1]: the comparison read names, types and required status and
 *  never looked at `constraints`, so a tree far larger than its declaration
 *  froze successfully. Whether the artifact's BYTES are what it claims is
 *  W2930's collection-time fact; the counts, totals and media type are
 *  already inside the document `validateManifest` accepted, and a limit that
 *  is decidable here and not decided here is a limit nobody enforces.
 *
 *  Only a `present` output is measured. An explicitly missing one carries no
 *  tree and no artifact, and measuring absence against a size would refuse it
 *  for being absent — which the declaration's `required` flag already decides
 *  on its own terms. */
function checkDeclaredLimits(name, expect, seen) {
	if (seen.status !== "present") {
		// AN OUTPUT THAT SAYS IT IS MISSING MUST BE MISSING. The schema
		// permits `missing-optional` beside a content manifest or an
		// artifact, and that combination is a document contradicting itself
		// — refused as the contradiction it is rather than resolved by
		// picking whichever half to believe.
		if (seen.content_manifest !== null || seen.artifact !== null) {
			throw new ContractError("integrity", "schema",
				`output ${name} reports ${seen.status} and carries material; `
				+ `a missing output is missing`);
		}
		return;
	}
	// AND `present` MUST BE PRESENT — the other direction of the same rule.
	//
	// Review [P1]: the correction refused a missing output that carried
	// material and left its converse open, so an output with neither a tree
	// nor an artifact froze as a satisfied REQUIRED output under a completed
	// disposition. A status word is not material. I had written down that a
	// comparison running one way is half a comparison, one round earlier, and
	// then enforced one direction of a two-directional rule.
	//
	// BOTH representations, per §8.4: a frozen result binds "every declared
	// output's content/tree digest AND artifact reference". The nullable
	// members exist so a MISSING output can say so, not so a present one can
	// choose which half to supply.
	if (seen.content_manifest === null || seen.artifact === null) {
		throw new ContractError("integrity", "schema",
			`output ${name} reports present and carries `
			+ `${seen.content_manifest === null ? "no content manifest" : "a content manifest"}`
			+ ` and `
			+ `${seen.artifact === null ? "no artifact reference" : "an artifact reference"}`
			+ `; a frozen result binds both for every declared output (§8.4)`);
	}
	const limits = expect.constraints;
	const content = seen.content_manifest;
	// BOTH SIZES, because the declaration bounds the output and a present
	// output has two representations of it. An earlier draft measured only
	// whichever one happened to be there, which after the rule above is
	// always the tree — leaving the artifact's declared size unbounded and
	// the fallback branch unreachable. An inert branch is either a decision
	// or a deletion.
	for (const [what, size] of [["tree", content.total_bytes],
	                            ["artifact", seen.artifact.bytes]]) {
		if (size > limits.max_bytes) {
			throw new ContractError("integrity", "limit",
				`output ${name} declares at most ${limits.max_bytes} bytes `
				+ `and its ${what} carries ${size}`);
		}
	}
	if (content.entry_count > limits.max_entries) {
		throw new ContractError("integrity", "limit",
			`output ${name} declares at most ${limits.max_entries} entries `
			+ `and the sealed result carries ${content.entry_count}`);
	}
	// LITERALLY, including the empty list. An allow-list that permits
	// everything when it names nothing is a fail-open reading of a rule
	// written to close.
	if (!limits.allowed_media_types.includes(seen.artifact.media_type)) {
		throw new ContractError("policy", "denied",
			`output ${name} carries media type ${seen.artifact.media_type}, `
			+ `which its declaration does not allow`);
	}
}
