// W2929 plan item 4, fourth slice: UPDATE NORMALIZATION.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance, frozen §6:
//
//   "A normalized agent event has a kind from exactly this set. `other` is
//    the deliberate escape hatch ... so that an update type this contract has
//    never seen is COUNTED rather than dropped or guessed at."
//
// COUNTED, NEVER GUESSED AT. An unmapped update is not a failure and it is
// not silence: it becomes `other`, keeps the provider's own kind string as
// diagnostics, and carries no portable content at all. A relay that guessed
// would be inventing agent evidence; a relay that dropped would be reporting
// a partial stream as a complete one.
//
// AND THE BYTES DO NOT COME IN. §6.3 admits `text` and `resource_link` and
// nothing else. Image, audio and embedded resource blocks are counted and
// their bytes dropped, because inlining agent-supplied bytes into a durable
// event turns an untrusted stream into permanent storage that every later
// reader has to re-validate.
//
// AND THE SEAL COVERS THE FRAME, NOT THE OBSERVING OF IT. §6.4 is explicit
// and the reason is concrete: `late` and the manager's `observation_seq` are
// properties of an OBSERVATION. A retransmitted frame is the same frame, so
// if lateness were sealed in, one frame seen twice — once before a turn ended
// and once after — would carry two digests, and an ordinary duplicate would
// be indistinguishable from a spliced stream. Lateness is decided when the
// frame is FIRST seen and a replay reports that original observation.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { assertNoDurableSecret, canonicalBytes, ContractError, digest,
         nameValue } from "./contracts.mjs";
import { certifiedAgentSessionProfile } from "./agent_profile.mjs";
import { normalizeAgentSessionRef } from "./agent_session_axis.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const AGENT_SESSION_SCHEMA = JSON.parse(readFileSync(
	join(HERE, "schema", "agent-session-1.0.schema.json")).toString("utf8"));

const _ajv = new Ajv2020({ strict: false, validateFormats: false,
                           allErrors: false });
// The shared `$id` is dropped for the same reason the turn module drops it:
// Ajv keys compiled schemas by it and refuses a second registration.
function definitionOf(name) {
	const { $id: _id, oneOf: _oneOf, ...rest } = AGENT_SESSION_SCHEMA;
	return { ...rest, $ref: `#/$defs/${name}` };
}

const _validateEvent = _ajv.compile(definitionOf("normalizedEvent"));

/** The closed ten. Every normalized event has exactly one of these. */
export const EVENT_KINDS = Object.freeze(["agent-message", "agent-reasoning",
	"tool-call", "tool-call-update", "plan", "mode-change", "usage",
	"session-info", "commands-changed", "other"]);

/** §6.2, transcribed in full. Thirteen rows, and nothing else maps at all.
 *
 *  Three rows are worth reading twice. `user_message_chunk` is `other`
 *  because the RELAY authored that prompt — an echo of it is the transport
 *  talking back, not the agent producing evidence. The three `plan` rows all
 *  land on one kind, because a plan, its supersession and its removal are
 *  entries about the same object rather than three different observations.
 *  And `agent_thought_chunk` is `agent-reasoning`, which §6.2 marks as
 *  diagnostics and never portable evidence. */
export const ACP_SESSION_UPDATES = Object.freeze({
	agent_message_chunk: "agent-message",
	agent_thought_chunk: "agent-reasoning",
	user_message_chunk: "other",
	tool_call: "tool-call",
	tool_call_update: "tool-call-update",
	plan: "plan",
	plan_update: "plan",
	plan_removed: "plan",
	current_mode_update: "mode-change",
	config_option_update: "other",
	session_info_update: "session-info",
	usage_update: "usage",
	available_commands_update: "commands-changed",
});

/** ACP's four tool-call statuses. §6.2: "status only from ACP's four". */
export const TOOL_CALL_STATUSES = Object.freeze(["pending", "in_progress",
	"completed", "failed"]);

/** The pinned ACP 1.3 `ToolKind` vocabulary, verbatim. §6.2.1 (W543).
 *
 *  The conflict this resolves: §6.2's prose required a portable `kind` while
 *  the frozen `toolCallView` forbade the member outright. The event slice
 *  declined to invent one while the two artefacts disagreed, and W543 ruled:
 *  `kind` is PORTABLE but OPTIONAL advisory evidence. The pinned SDK declares
 *  `kind?: ToolKind` on a tool call and `kind?: ToolKind | null` on an
 *  update — permitted, never required.
 *
 *  A value outside this list REFUSES rather than silently widening a frozen
 *  contract. Supporting a later ACP vocabulary is explicit
 *  version/certification work, not something a provider does by sending a
 *  word this manager has not seen. */
export const TOOL_KINDS = Object.freeze(["read", "edit", "delete", "move",
	"search", "execute", "think", "fetch", "switch_mode", "other"]);

/** The kinds that carry NO portable content, whatever the update held.
 *
 *  §6.1 says `other` "carries only the source kind string plus its bounded
 *  diagnostics". That is a rule and not a description: `user_message_chunk`
 *  arrives WITH content and still becomes `other`, so a normalizer that
 *  passed content through whenever it happened to be present would quietly
 *  make the relay's own prompt into durable agent evidence. The bytes are
 *  still COUNTED — that is the whole point of the escape hatch.
 *
 *  Review [P1]: `agent-reasoning` belongs here too and I had left it out.
 *  §6.2 marks `agent_thought_chunk` content "diagnostics; never portable
 *  evidence", which is the same sentence about a different member — a chain
 *  of thought placed in an event's portable `content` is exactly the durable
 *  agent evidence that row forbids. Counted, like every other body this
 *  boundary declines to carry. */
const CONTENTLESS_KINDS = Object.freeze(["other", "agent-reasoning"]);

/** The block types whose BYTES never become durable. §6.3. */
const DROPPED_BLOCK_TYPES = Object.freeze({ image: "image", audio: "audio",
                                            resource: "resource" });

/** Count encoded UTF-8 bytes, which is what every limit in §3.1 is in. */
function utf8Bytes(value) {
	return Buffer.byteLength(JSON.stringify(value ?? null), "utf8");
}

/** One source content block, normalized or counted-and-dropped.
 *
 *  §6.3 admits exactly `text` and `resource_link`. Everything else is
 *  recorded as its type and its byte count with the bytes gone — including a
 *  type this contract has never seen, which becomes `unknown` rather than
 *  being discarded. A dropped block that left no trace would turn a partial
 *  record into an apparently complete one, which is the same failure the
 *  overflow record exists to prevent one level up. */
function normalizeBlock(block, at) {
	const type = block?.type;
	if (type === "text") {
		if (typeof block.text !== "string") {
			throw new ContractError("integrity", "schema",
				`content block ${at} is a text block whose text is `
				+ `${typeof block.text}`);
		}
		return { type: "text", text: block.text };
	}
	if (type === "resource_link") {
		if (typeof block.uri !== "string" || typeof block.name !== "string") {
			throw new ContractError("integrity", "schema",
				`content block ${at} is a resource link without a string uri `
				+ `and name`);
		}
		return { type: "resource_link", uri: block.uri, name: block.name };
	}
	// COUNTED, THEN DROPPED. The count is of the block as it arrived, so a
	// reader can tell how much was withheld rather than only that something
	// was.
	return { type: "dropped",
	         dropped_type: DROPPED_BLOCK_TYPES[type] ?? "unknown",
	         byte_count: utf8Bytes(block ?? null) };
}

/** The tool call an ACP update carries, read where ACP actually puts it.
 *
 *  Review [P1]: I read `update.toolCall.toolCallId`. The frozen captured
 *  trace carries `toolCallId` and `status` at the UPDATE ROOT for both
 *  `tool_call` and `tool_call_update`, so the normalizer refused the very
 *  provider shape it was built to normalize. A mapping table is only half the
 *  contract; the captured evidence is where the other half lives.
 *
 *  ACP's `kind` is carried when the provider GIVES one — §6.2.1, the W543
 *  correction. It is copied verbatim and the member is OMITTED otherwise.
 *
 *  BATON NEVER INVENTS A KIND. Absence does not become `other`, and no title,
 *  tool name, command text, adapter family or later status may be used to
 *  infer one. A missing kind is missing evidence, and the difference between
 *  "the provider said this was a read" and "we guessed it was a read" is the
 *  whole value of the member.
 *
 *  Review [P1]: AND THE TWO SOURCES DO NOT ADMIT THE SAME SHAPES. I wrote
 *  the SDK's declaration into the comment above -- `kind?: ToolKind` on a
 *  tool call, `kind?: ToolKind | null` on an update -- and then treated null
 *  as absence on BOTH, which erases the only difference the declaration
 *  states. An OMITTED member is absence on either source. An explicit null is
 *  the SDK's own "not supplied" on `tool_call_update` and is absence there;
 *  on the initial `tool_call` it is a shape the pinned type does not admit,
 *  so it refuses. Documenting a distinction is not implementing it.
 *
 *  Review [P2]: AND A REFUSAL DOES NOT SERIALIZE WHAT IT IS REFUSING. This
 *  message interpolated `JSON.stringify(update.kind)`, so a BigInt left the
 *  boundary as a raw `TypeError` instead of the closed pair -- the diagnostic
 *  broke the taxonomy the check exists to enforce. The value's SHAPE is
 *  tested before its membership, and the message names the shape and the
 *  vocabulary rather than echoing a value this boundary has just rejected.
 *
 *  And it decides nothing. The ruling is explicit that the field may support
 *  presentation — a category label or an icon, which is the use the SDK's own
 *  declaration names — and decides no permission, policy, tool authority,
 *  turn outcome, success, failure or disposition. Nothing in this manager
 *  reads it, which is the implementation of that sentence. */
function normalizeToolCall(update, kind, sourceKind) {
	if (kind !== "tool-call" && kind !== "tool-call-update") return null;
	const id = update?.toolCallId;
	const status = update?.status;
	if (typeof id !== "string" || id.length === 0) {
		throw new ContractError("integrity", "schema",
			`a ${kind} update carries no toolCallId; the identity is the `
			+ `provider's and this boundary never mints one`);
	}
	if (!TOOL_CALL_STATUSES.includes(status)) {
		throw new ContractError("integrity", "schema",
			`${nameValue(status)} is not one of ACP's four tool-call `
			+ `statuses (${TOOL_CALL_STATUSES.join(", ")})`);
	}
	const view = { tool_call_id: id, status };
	if (typeof update.title === "string") view.title = update.title;
	// Read the member ONCE. A shifting getter must not be able to make the
	// refusal and the copy disagree about what the provider sent.
	const supplied = update.kind;
	if (supplied === undefined) return view;
	if (supplied === null) {
		// Absence on an update, a shape the initial call does not admit.
		if (sourceKind !== "tool_call_update") {
			throw new ContractError("integrity", "schema",
				`only tool_call_update declares kind?: ToolKind | null; a `
				+ `${sourceKind} declares kind?: ToolKind and does not admit `
				+ `null, so an explicit null here is a shape the pinned ACP `
				+ `1.3 SDK refuses rather than the provider omitting the `
				+ `member`);
		}
		return view;
	}
	// SHAPE BEFORE MEMBERSHIP, and the message names neither the value nor
	// its serialization: `typeof` cannot run provider code and cannot fail.
	if (typeof supplied !== "string" || !TOOL_KINDS.includes(supplied)) {
		throw new ContractError("integrity", "schema",
			`a tool-call kind is one of the pinned ACP 1.3 ToolKinds `
			+ `(${TOOL_KINDS.join(", ")}); this ${sourceKind} carried a `
			+ `${typeof supplied} that is not one of them. A later vocabulary `
			+ `needs explicit version/certification work rather than a `
			+ `provider widening this one by sending a new word`);
	}
	view.kind = supplied;
	return view;
}

/** Normalize ONE ACP session update into the portable shape. Pure.
 *
 *  Returns the portable members only — the frame around them is built by
 *  `sealEvent`, because a normalizer that also identified and sealed would be
 *  two boundaries wearing one name. */
export function normalizeAcpUpdate(update) {
	const sourceKind = update?.sessionUpdate;
	if (typeof sourceKind !== "string" || sourceKind.length === 0) {
		throw new ContractError("integrity", "schema",
			`an ACP session update names its own kind in \`sessionUpdate\`; `
			+ `this one carries ${nameValue(sourceKind)}`);
	}
	// UNMAPPED IS `other`, NOT A REFUSAL. §6.1 exists so an update type this
	// contract has never seen is counted.
	const kind = ACP_SESSION_UPDATES[sourceKind] ?? "other";
	const blocks = Array.isArray(update.content) ? update.content
		: update.content === undefined || update.content === null ? []
		: [update.content];
	const content = CONTENTLESS_KINDS.includes(kind)
		? [] : blocks.map(normalizeBlock);
	return { kind, sourceKind, content,
	         toolCall: normalizeToolCall(update, kind, sourceKind),
	         byteCount: utf8Bytes(update) };
}

/** The pinned event limit for the profile this session opened under. */
function eventLimit(store, session) {
	const profile = certifiedAgentSessionProfile(store, session.profile_digest);
	if (profile === null) {
		throw new ContractError("refused", "precondition",
			`the profile ${session.profile_digest} this session opened under `
			+ `is no longer certified; a bound nobody can read is not a bound`);
	}
	return profile.limits.max_event_bytes;
}

/** Take durable ownership of a caller's value, or report the closed pair.
 *
 *  Re-review [P2]: `structuredClone` ran straight over content, tool-call
 *  data and diagnostics, so a non-cloneable member escaped as a raw
 *  `DataCloneError`. The outer taxonomy is closed and unnormalizable event
 *  content belongs to `integrity.schema`; a provider-facing caller cannot map
 *  an interpreter exception onto that wire contract without re-deriving
 *  policy it was never given.
 *
 *  An existing `ContractError` passes through UNCHANGED, so a more precise
 *  canonical failure is not flattened into this general one.
 *
 *  MEASURED AS UNREACHABLE HERE, and said rather than implied: nothing inside
 *  `structuredClone` raises a `ContractError`, so removing that line changes
 *  no case. It is kept for symmetry with the SEAL wrapper below, where the
 *  same line is load-bearing because `canonicalBytes` refuses several
 *  representations by name — negative zero, a non-finite number, a lone
 *  surrogate. It is not counted as a guard. */
function ownDurable(value, where) {
	try {
		return structuredClone(value);
	} catch (failure) {
		if (failure instanceof ContractError) throw failure;
		throw new ContractError("integrity", "schema",
			`${where} carries a value this boundary cannot own `
			+ `(${failure.message}); a normalized event is durable JSON`);
	}
}

/** Build and SEAL one normalized event frame.
 *
 *  The frame carries what the relay saw. It does NOT carry `late` or
 *  `observation_seq`: those belong to the act of observing it, they are
 *  decided by `observeEvent` and they live beside the document. */
export function sealEvent({ sessionRef, sourceSeq, observedAt, turnId = null,
                            kind, sourceKind, content = [], toolCall = null,
                            byteCount, adapterDiagnostics = {} }) {
	if (!EVENT_KINDS.includes(kind)) {
		throw new ContractError("integrity", "schema",
			`${nameValue(kind)} is not one of the ten normalized event `
			+ `kinds`);
	}
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "event",
		agent_session_ref: {
			runtime_attempt_id: sessionRef?.runtimeAttemptId,
			posture: sessionRef?.posture,
			session_epoch: sessionRef?.sessionEpoch,
			provider_session_id: sessionRef?.providerSessionId ?? null,
		},
		source_seq: sourceSeq,
		observed_at: observedAt,
		turn_id: turnId,
		kind,
		source_kind: sourceKind,
		content: ownDurable(content, "event content"),
		tool_call: toolCall === null
			? null : ownDurable(toolCall, "the tool call"),
		byte_count: byteCount,
		// A CONSTANT IN THE FROZEN SHAPE, and therefore a claim this boundary
		// has to be able to make. §9 redaction is what makes it true, and
		// `observeEvent` scans the complete document before anything durable
		// happens — asserting it here and checking it nowhere would be the
		// document lying about itself.
		redacted: true,
		adapter_diagnostics: ownDurable(adapterDiagnostics,
		                                "adapter diagnostics"),
	};
	// The SEAL is the other place a caller's value becomes durable, and
	// `canonicalBytes` refuses several representations by name. Its refusals
	// are already closed pairs and are kept exactly as they are.
	let sealed;
	try {
		sealed = digest(body);
	} catch (failure) {
		if (failure instanceof ContractError) throw failure;
		throw new ContractError("integrity", "schema",
			`this event has no canonical representation (${failure.message})`);
	}
	const document = { ...body, document_digest: sealed };
	if (!_validateEvent(document)) {
		const first = _validateEvent.errors?.[0];
		throw new ContractError("integrity", "schema",
			`this event is not a valid baton.agent-session 1.0 event: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	return document;
}

function sessionRow(db, ref) {
	const session = db.prepare(
		"SELECT state, profile_digest, provider_session_id FROM agent_sessions "
		+ "WHERE runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
		.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch);
	if (session === undefined) {
		throw new ContractError("refused", "precondition",
			`no agent session ${ref.posture}/${ref.sessionEpoch} for attempt `
			+ `${ref.runtimeAttemptId}; an event happens INSIDE one`);
	}
	return session;
}

/** The reference an event claims, proven and owned. */
function eventSessionRef(document) {
	const ref = document?.agent_session_ref;
	return { runtimeAttemptId: ref?.runtime_attempt_id, posture: ref?.posture,
	         sessionEpoch: ref?.session_epoch,
	         providerSessionId: ref?.provider_session_id ?? null };
}

/** Whether this frame arrived after its turn already had a terminal fact.
 *
 *  §6.4: a late event "never reopens the turn, never changes the turn outcome,
 *  and never contributes to a disposition". It is recorded and marked, which
 *  is the whole of what lateness does. A frame naming no turn is not late —
 *  there is no terminal fact for it to be after. */
function decideLate(db, turnId) {
	if (turnId === null) return false;
	return db.prepare("SELECT 1 AS present FROM turns WHERE turn_id = ?")
		.get(turnId) !== undefined;
}

/** Observe one sealed frame into the durable record.
 *
 *  Returns `{ sourceSeq, observationSeq, late, replayed, documentDigest }` —
 *  the frame's identity plus the three facts that belong to OBSERVING it.
 *
 *  The duplicate rule is §6.4's and the comparison is the seal: both sides
 *  are sealed, so the two `document_digest` values ARE the comparison and
 *  nothing has to be reconstructed to make it. */
export function observeEvent(store, document, options = {}) {
	// THE SEAL BEFORE ANY OTHER FIELD. §6.4: "a consumer verifies that seal
	// BEFORE it reads any other field", and an event whose digest was never
	// checked has no claim on any rule below — including the identity and
	// duplicate rules this function is about to apply.
	const owned = authenticateEvent(document);
	const ref = eventSessionRef(owned);
	// THE SEALED FRAME OWNS ITS TURN. Review [P1]: a separate operand
	// defaulted to null, the sealed `turn_id` was checked only when that
	// operand happened to be non-null, and the OPERAND was what got written —
	// so a frame sealed for a turn became a durable unbound event whenever a
	// caller omitted the option, losing an authenticated identity member and
	// giving lateness the wrong subject. The document decides; a redundant
	// operand may only agree, in both directions.
	const turnId = owned.turn_id;
	if ("turnId" in options && (options.turnId ?? null) !== turnId) {
		throw new ContractError("runtime-observation", "identity-mismatch",
			`the sealed frame names turn ${JSON.stringify(turnId)} and it is `
			+ `being observed into ${nameValue(options.turnId ?? null)}`);
	}
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	try {
		const session = sessionRow(db, ref);
		// §6.4: an event whose reference is not this session's is an
		// identity mismatch, and §3.1 says the reference is the FULL one.
		const stored = session.provider_session_id ?? null;
		if (stored !== ref.providerSessionId) {
			throw new ContractError("runtime-observation", "identity-mismatch",
				`this event names provider session `
				+ `${JSON.stringify(ref.providerSessionId)} and epoch `
				+ `${ref.posture}/${ref.sessionEpoch} durably names `
				+ `${JSON.stringify(stored)}`);
		}
		const prior = db.prepare(
			"SELECT observation_seq, late, body, document_digest "
			+ "FROM agent_events "
			+ "WHERE runtime_attempt_id = ? AND posture = ? "
			+ "AND session_epoch = ? AND source_seq = ?")
			.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch,
			     owned.source_seq);
		if (prior !== undefined) {
			// SAME FRAME: replay the ORIGINAL observation. Its lateness was
			// decided when it was first seen, and minting a new answer here
			// is exactly what §6.4 forbids.
			if (prior.document_digest === owned.document_digest) {
				// FROM DURABLE STATE, AUTHENTICATED. Review [P1]: this
				// compared an index digest and answered with metadata,
				// so a retained body that had become unreadable was
				// reported as a successful replay. A duplicate is an
				// answer from the record, not permission to trust the
				// column that indexes it.
				const retained = authenticateRetained(prior, owned.source_seq,
				                                      ref);
				db.exec("COMMIT");
				return { sourceSeq: owned.source_seq,
				         observationSeq: prior.observation_seq,
				         late: prior.late === 1, replayed: true,
				         documentDigest: owned.document_digest,
				         document: retained };
			}
			throw new ContractError("integrity", "digest",
				`source sequence ${owned.source_seq} of `
				+ `${ref.posture}/${ref.sessionEpoch} is already sealed under `
				+ `${prior.document_digest} and this frame seals to `
				+ `${owned.document_digest}; the transport lied about ordering `
				+ `or the stream was spliced, and neither is a merge to `
				+ `attempt`);
		}
		// A NEW FRAME. Bounds and redaction before anything durable, because
		// the relay is the trust boundary and §6.3 says the check happens
		// here rather than downstream.
		// THE EVENT, MEASURED. Review [P1]: this compared `byte_count`, which
		// is an accounting member INSIDE the untrusted sealed document — it
		// describes the source update, and a frame may claim 1 while the
		// event itself is far over the bound. The frozen model measures
		// `canonical_bytes(event)` and §6.3 bounds every normalized EVENT, so
		// the thing being bounded is what gets measured. `byte_count` keeps
		// its own job: saying how much source there was, including the parts
		// that were dropped.
		const limit = eventLimit(store, session);
		const measured = canonicalBytes(owned).length;
		if (measured > limit) {
			throw new ContractError("integrity", "limit",
				`this event is ${measured} canonical bytes and the profile `
				+ `pins ${limit}; §3.1 refuses over-limit input without `
				+ `partial action`);
		}
		assertNoDurableSecret(owned, `event ${owned.source_seq}`);
		if (turnId !== null) {
			const allocated = db.prepare(
				"SELECT runtime_attempt_id, posture, session_epoch FROM "
				+ "turn_allocations WHERE turn_token = ?").get(turnId);
			if (allocated === undefined
					|| allocated.runtime_attempt_id !== ref.runtimeAttemptId
					|| allocated.posture !== ref.posture
					|| allocated.session_epoch !== ref.sessionEpoch) {
				throw new ContractError("runtime-observation",
					"identity-mismatch",
					`${turnId} is not a turn allocated in `
					+ `${ref.posture}/${ref.sessionEpoch}`);
			}
		}
		const late = decideLate(db, turnId);
		// The MANAGER's ordering, per epoch, exactly as the runtime
		// observations already assign theirs per attempt.
		const observationSeq = db.prepare(
			"SELECT COALESCE(MAX(observation_seq), 0) + 1 AS next FROM "
			+ "agent_events WHERE runtime_attempt_id = ? AND posture = ? "
			+ "AND session_epoch = ?")
			.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch).next;
		db.prepare(
			"INSERT INTO agent_events (runtime_attempt_id, posture, "
			+ "session_epoch, source_seq, observation_seq, turn_id, kind, "
			+ "source_kind, byte_count, late, body, document_digest, "
			+ "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch,
			     owned.source_seq, observationSeq, turnId, owned.kind,
			     owned.source_kind, owned.byte_count, late ? 1 : 0,
			     canonicalBytes(owned).toString("utf8"), owned.document_digest,
			     store.clock());
		db.exec("COMMIT");
		// OWNED, AND THE SAME SEALED BYTES. §6.4 requires the consumer to
		// answer with the bytes it sealed and to return copies rather than
		// the submitted object.
		//
		// MEASURED AS EQUIVALENT, and said rather than implied: `owned` is
		// ALREADY a fresh object, because `authenticateEvent` reached it
		// through a serialize/parse round-trip — that is what makes the
		// answer owned, not this line, and returning `owned` directly passes
		// every case. The clone is kept because a boundary that hands back
		// the object it is still holding is how a later edit here becomes a
		// caller's surprise, and it is not counted as a guard.
		return { sourceSeq: owned.source_seq, observationSeq, late,
		         replayed: false, documentDigest: owned.document_digest,
		         document: structuredClone(owned) };
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
}

/** Shape, seal and self-consistency, before any other field is read. */
function authenticateEvent(document) {
	let owned;
	try {
		owned = JSON.parse(JSON.stringify(document ?? null));
	} catch (failure) {
		throw new ContractError("integrity", "schema",
			`this event has no durable representation (${failure.message})`);
	}
	if (!_validateEvent(owned)) {
		const first = _validateEvent.errors?.[0];
		throw new ContractError("integrity", "schema",
			`this event is not a valid baton.agent-session 1.0 event: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	const { document_digest: declared, ...rest } = owned;
	const recomputed = digest(rest);
	if (recomputed !== declared) {
		throw new ContractError("integrity", "digest",
			`this event declares ${declared} and its canonical bytes `
			+ `recompute to ${recomputed}`);
	}
	return owned;
}

/** One retained row, parsed fresh and re-bound to everything that identifies
 *  it: its shape, the digest it declares, the digest its bytes recompute to,
 *  the digest it is filed under, and the sequence the caller asked for.
 *
 *  Shared by the reader and by the REPLAY path, deliberately. Review [P1]: a
 *  duplicate answered from the indexed digest column alone, so a body that
 *  had become unreadable was reported as a successful replay — the one place
 *  a stale index is most convincing is the place a record is not read.
 *
 *  Re-review [P1]: and the requested SESSION is a fifth witness. The row is
 *  selected on attempt, posture and epoch, so a caller asking for provider
 *  session B was handed a frame sealed for provider session A whenever the
 *  other three agreed — the same identity mismatch the write path refuses,
 *  reached through the read path instead. §3.1 makes the provider session id
 *  part of the reference, so binding three quarters of it is not binding it.
 *
 *  MEASURED: from the replay path this comparison is INERT, because the
 *  retained and incoming digests are already equal there and equal digests
 *  mean equal references. It is one function because the rule is one rule,
 *  and the reader is where it has teeth. */
function authenticateRetained(row, sourceSeq, requested) {
	let owned;
	try {
		owned = JSON.parse(row.body);
	} catch (failure) {
		throw new ContractError("integrity", "digest",
			`the retained event at source sequence ${sourceSeq} is not `
			+ `parsable (${failure.message}); bytes that cannot be read cannot `
			+ `be bound to the digest they were sealed under`);
	}
	if (!_validateEvent(owned)) {
		throw new ContractError("integrity", "schema",
			`the retained event at source sequence ${sourceSeq} is not a valid `
			+ `event record`);
	}
	const { document_digest: declared, ...rest } = owned;
	const recomputed = digest(rest);
	if (recomputed !== row.document_digest
			|| declared !== row.document_digest) {
		throw new ContractError("integrity", "digest",
			`the event at source sequence ${sourceSeq} is sealed under `
			+ `${row.document_digest}, declares ${declared} and recomputes to `
			+ `${recomputed}`);
	}
	if (owned.source_seq !== sourceSeq) {
		throw new ContractError("integrity", "digest",
			`the frame filed at source sequence ${sourceSeq} calls itself `
			+ `${owned.source_seq}`);
	}
	const held = eventSessionRef(owned);
	if (held.runtimeAttemptId !== requested.runtimeAttemptId
			|| held.posture !== requested.posture
			|| held.sessionEpoch !== requested.sessionEpoch
			|| held.providerSessionId !== requested.providerSessionId) {
		throw new ContractError("runtime-observation", "identity-mismatch",
			`the frame at source sequence ${sourceSeq} is sealed for `
			+ `${JSON.stringify(held)} and was asked for as `
			+ `${JSON.stringify(requested)}`);
	}
	return owned;
}

/** The retained frame for one epoch sequence, or null — re-bound to the seal
 *  and to the sequence it is filed under. */
export function eventRecordOf(store, sessionRef, sourceSeq) {
	// W2929 composition revalidation: THE OPERANDS ARE PROVED BEFORE THEY
	// REACH THE STATEMENT. Measured — the four members went from an unproved
	// reference straight into the query, so a caller handing this reader an
	// object or a BigInt got SQLite's own binding error instead of the closed
	// pair, at a read that had validated nothing.
	//
	// The reference is proved by §3.1's own normalizer, which is where that
	// rule already lives, and the ONE OWNED COPY it returns is what both the
	// query and the retained-document binding use. Reading the members twice
	// is how the check and the answer come to disagree.
	//
	// A well-formed reference naming no frame still answers null. Absence and
	// refusal are different answers to different questions.
	const requested = normalizeAgentSessionRef(sessionRef);
	if (!Number.isInteger(sourceSeq) || sourceSeq < 1) {
		throw new ContractError("integrity", "schema",
			`${nameValue(sourceSeq)} is not a provider source sequence; an `
			+ `operand is proved before it reaches the store`);
	}
	const row = store.db.prepare(
		"SELECT body, document_digest, observation_seq, late FROM agent_events "
		+ "WHERE runtime_attempt_id = ? AND posture = ? AND session_epoch = ? "
		+ "AND source_seq = ?")
		.get(requested.runtimeAttemptId, requested.posture,
		     requested.sessionEpoch, sourceSeq);
	// A genuinely absent `(attempt, posture, epoch, source_seq)` is null. A
	// PRESENT row whose sealed reference disagrees is a mismatch and not an
	// absence: answering null there would tell a caller no such frame exists
	// while the epoch holds one.
	if (row === undefined) return null;
	// The OBSERVATION travels beside the document, never inside it.
	return { document: authenticateRetained(row, sourceSeq, requested),
	         observationSeq: row.observation_seq, late: row.late === 1 };
}
