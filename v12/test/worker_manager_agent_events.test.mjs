// W2929 item 4, fourth slice: update normalization.
//
// The contract's escape hatch is the interesting part, so most of these cases
// are about an update this boundary has never seen being COUNTED rather than
// dropped or guessed at — and the two tables are driven EXHAUSTIVELY in both
// directions, because a closed set checked at three of ten points is a closed
// set nobody has checked.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, GOLDEN_BEARER, canonicalBytes, digest }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { AGENT_SESSION_SCHEMA_PATH, certifyAgentSessionProfile }
	from "../src/worker_manager/agent_profile.mjs";
import { allocateTurn, recordTurn }
	from "../src/worker_manager/agent_turn.mjs";
import { ACP_SESSION_UPDATES, EVENT_KINDS, TOOL_CALL_STATUSES, TOOL_KINDS,
         eventRecordOf, normalizeAcpUpdate, observeEvent, sealEvent }
	from "../src/worker_manager/agent_events.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const REF = { runtimeAttemptId: ATTEMPT, posture: "execution",
              sessionEpoch: 1, providerSessionId: null };

const SESSION_STATES = JSON.parse(
	readFileSync(AGENT_SESSION_SCHEMA_PATH).toString("utf8"))
	.$defs.sessionState.enum;

/** The one certified profile these cases open sessions under. Its
 *  `max_event_bytes` is deliberately small, so the bound is reachable by a
 *  case rather than only by a comment. */
const PROFILE = (() => {
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "profile",
		profile_id: "profile-events-1",
		created_at: NOW,
		wire_protocol: "acp",
		pinned_wire_version: 1,
		provider_binding: null,
		adapter: { name: "scripted", version: "1.0-test",
		           build_digest: digest("adapter") },
		client_capabilities: { fs: {}, terminal: false },
		session_capabilities: ["session.cancel", "session.fresh",
			"session.mode-pin", "session.permission-refusal", "session.prompt",
			"session.update-normalization"],
		postures: {
			consent: { policy: { kind: "acp", session_mode_id: "plan" },
			           workspace: false, declared_output: false },
			execution: { policy: { kind: "acp",
			                       session_mode_id: "acceptEdits" },
			             workspace: true, declared_output: true },
		},
		mcp_servers: [],
		limits: { setup_deadline_ms: 120000, turn_deadline_ms: 900000,
		          cancel_drain_deadline_ms: 30000, max_event_bytes: 900,
		          max_queue_events: 1024, max_queue_bytes: 4194304 },
		agent_policy_digest: digest("policy"),
	};
	return { ...body, document_digest: digest(body) };
})();

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

/** An attempt, the certified profile, and one open execution session. */
function withSession(store, extra = {}) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"),
		profileDigest: PROFILE.document_digest });
	certifyAgentSessionProfile(store, PROFILE);
	store.db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, provider_session_id, state, opened_at) "
		+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?)")
		.run(ATTEMPT, extra.posture ?? REF.posture,
		     extra.sessionEpoch ?? REF.sessionEpoch, PROFILE.document_digest,
		     digest("policy"), WORK, UUID, extra.providerSessionId ?? null,
		     NOW);
	return { ...REF, ...extra };
}

function frame(overrides = {}) {
	const update = overrides.update
		?? { sessionUpdate: "agent_message_chunk",
		     content: [{ type: "text", text: "hello" }] };
	const portable = normalizeAcpUpdate(update);
	return sealEvent({ sessionRef: overrides.sessionRef ?? REF,
		// `in` rather than `??`, so a case can drive an explicitly null or
		// zero sequence instead of silently getting the default.
		sourceSeq: "sourceSeq" in overrides ? overrides.sourceSeq : 1,
		observedAt: overrides.observedAt ?? NOW,
		turnId: overrides.turnId ?? null,
		kind: overrides.kind ?? portable.kind,
		sourceKind: overrides.sourceKind ?? portable.sourceKind,
		content: overrides.content ?? portable.content,
		toolCall: overrides.toolCall ?? portable.toolCall,
		byteCount: overrides.byteCount ?? portable.byteCount,
		adapterDiagnostics: overrides.adapterDiagnostics ?? {} });
}

// -- the closed set and its one mapping table --------------------------------

test("W2929: the ten normalized kinds are the ten, and the map lands in them",
	() => {
		assert.deepEqual([...EVENT_KINDS], ["agent-message", "agent-reasoning",
			"tool-call", "tool-call-update", "plan", "mode-change", "usage",
			"session-info", "commands-changed", "other"]);
		// §6.2, transcribed verbatim — all thirteen rows.
		assert.deepEqual(ACP_SESSION_UPDATES, {
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
		// EXHAUSTIVE, in both directions: every row lands in the closed set,
		// and every kind the set names is reachable except the two the table
		// never produces from an ACP update.
		const reached = new Set();
		for (const [update, kind] of Object.entries(ACP_SESSION_UPDATES)) {
			assert.equal(EVENT_KINDS.includes(kind), true, update);
			reached.add(kind);
		}
		assert.deepEqual(EVENT_KINDS.filter((kind) => !reached.has(kind)), [],
			"a normalized kind is unreachable from the frozen ACP mapping");
	});

test("W2929: every mapped update normalizes to its exact row", () => {
	for (const [sourceKind, kind] of Object.entries(ACP_SESSION_UPDATES)) {
		const update = { sessionUpdate: sourceKind };
		if (kind === "tool-call" || kind === "tool-call-update") {
			// MIGRATED on the review's authority: the frozen captured trace
			// puts `toolCallId` and `status` at the UPDATE ROOT. This is a
			// fixture correction to the shape ACP actually sends; the
			// assertions below are unchanged.
			Object.assign(update, { toolCallId: "t1", status: "pending" });
		}
		const portable = normalizeAcpUpdate(update);
		assert.equal(portable.kind, kind, sourceKind);
		// The provider's own word is retained verbatim, which is what makes
		// three plan rows distinguishable after they land on one kind.
		assert.equal(portable.sourceKind, sourceKind);
	}
});

test("W2929: an update this contract has never seen is COUNTED, not guessed",
	() => {
		const update = { sessionUpdate: "quantum_entanglement_update",
		                 content: [{ type: "text", text: "some prose" }] };
		const portable = normalizeAcpUpdate(update);
		assert.equal(portable.kind, "other");
		// The escape hatch keeps the source kind and nothing else — §6.1 says
		// `other` carries only that string plus bounded diagnostics.
		assert.equal(portable.sourceKind, "quantum_entanglement_update");
		assert.deepEqual(portable.content, []);
		assert.equal(portable.toolCall, null);
		// COUNTED. The bytes are gone and the fact that there were bytes is
		// not: that is the whole difference between this and a drop.
		assert.equal(portable.byteCount > 0, true);
	});

test("W2929: `other` carries no portable content even when the update had some",
	() => {
		// `user_message_chunk` is the case that makes this a rule rather than
		// a description: the RELAY authored that prompt, so an echo of it is
		// the transport talking back and must never become durable agent
		// evidence.
		const portable = normalizeAcpUpdate({
			sessionUpdate: "user_message_chunk",
			content: [{ type: "text", text: "the prompt we sent" }] });
		assert.equal(portable.kind, "other");
		assert.deepEqual(portable.content, []);
		assert.equal(portable.byteCount > 0, true, "the echo was not counted");
	});

test("W2929 review: agent reasoning content remains diagnostic-only", () => {
	const portable = normalizeAcpUpdate({
		sessionUpdate: "agent_thought_chunk",
		content: [{ type: "text", text: "private chain of thought" }] });
	assert.equal(portable.kind, "agent-reasoning");
	assert.deepEqual(portable.content, [],
		"§6.2 diagnostic reasoning became portable evidence");
	assert.equal(portable.byteCount > 0, true, "the diagnostic was not counted");
});

test("W2929: an update that names no kind is refused", () => {
	for (const [what, update] of [["absent", {}],
	                              ["null", { sessionUpdate: null }],
	                              ["empty", { sessionUpdate: "" }],
	                              ["a number", { sessionUpdate: 7 }],
	                              ["no update", undefined]]) {
		assert.throws(() => normalizeAcpUpdate(update),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", what);
	}
});

// -- content restrictions ----------------------------------------------------

test("W2929: text and resource links come in, and nothing else does", () => {
	const portable = normalizeAcpUpdate({
		sessionUpdate: "agent_message_chunk",
		content: [
			{ type: "text", text: "prose" },
			{ type: "resource_link", uri: "file:///w/a.txt", name: "a.txt",
			  extra: "ignored" },
		] });
	assert.deepEqual(portable.content, [
		{ type: "text", text: "prose" },
		// The link is REBUILT from its three admitted members, so a member
		// the frozen block does not name cannot ride along into the seal.
		{ type: "resource_link", uri: "file:///w/a.txt", name: "a.txt" },
	]);
});

test("W2929: image, audio and embedded resource bytes are counted and dropped",
	() => {
		// Inlining agent-supplied bytes into a durable event turns an
		// untrusted stream into permanent storage every later reader has to
		// re-validate. So the type and the size survive and the bytes do not.
		const bytes = "A".repeat(64);
		for (const [type, dropped] of [["image", "image"], ["audio", "audio"],
		                               ["resource", "resource"],
		                               ["hologram", "unknown"],
		                               [undefined, "unknown"]]) {
			const portable = normalizeAcpUpdate({
				sessionUpdate: "agent_message_chunk",
				content: [{ type, data: bytes }] });
			assert.equal(portable.content.length, 1, String(type));
			const block = portable.content[0];
			assert.equal(block.type, "dropped", String(type));
			assert.equal(block.dropped_type, dropped, String(type));
			assert.equal(block.byte_count > 64, true, String(type));
			assert.equal("data" in block, false, "the bytes survived the drop");
		}
	});

test("W2929: a malformed admitted block is refused rather than half-read", () => {
	for (const [what, block] of [
			["text without text", { type: "text" }],
			["text that is a number", { type: "text", text: 7 }],
			["a link without a name", { type: "resource_link",
			                            uri: "file:///w/a" }],
			["a link without a uri", { type: "resource_link", name: "a" }]]) {
		assert.throws(() => normalizeAcpUpdate({
			sessionUpdate: "agent_message_chunk", content: [block] }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", what);
	}
});

test("W2929: a tool call carries the provider's id and ONE of ACP's four", () => {
	assert.deepEqual([...TOOL_CALL_STATUSES],
		["pending", "in_progress", "completed", "failed"]);
	// MIGRATED on the review's authority: the frozen captured trace carries
	// `toolCallId` and `status` at the UPDATE ROOT for both tool-call kinds.
	// Every id and status assertion below is the one this case already made.
	for (const status of TOOL_CALL_STATUSES) {
		for (const sourceKind of ["tool_call", "tool_call_update"]) {
			const portable = normalizeAcpUpdate({ sessionUpdate: sourceKind,
				toolCallId: "call-1", status, title: "grep" });
			assert.deepEqual(portable.toolCall,
				{ tool_call_id: "call-1", status, title: "grep" }, status);
		}
	}
	for (const [what, fields] of [
			["a fifth status", { toolCallId: "c", status: "cancelled" }],
			["no status", { toolCallId: "c" }],
			["no id", { status: "pending" }],
			["an empty id", { toolCallId: "", status: "pending" }],
			["nothing at all", {}]]) {
		assert.throws(() => normalizeAcpUpdate({ sessionUpdate: "tool_call",
			...fields }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", what);
	}
	// And a kind that is not a tool call never acquires one, whatever the
	// update happened to carry.
	assert.equal(normalizeAcpUpdate({ sessionUpdate: "plan",
		toolCallId: "c", status: "pending" }).toolCall, null);
	// SUPERSEDED ASSERTION, on W543's ruling. This used to require that a
	// supplied `kind` be DISCARDED, because §6.2's prose named the member and
	// the frozen `toolCallView` forbade it and this slice would not pick a
	// winner between two frozen artefacts. W543 picked: `kind` is portable
	// and optional. It is copied now, and the cases below own that contract.
	assert.deepEqual(normalizeAcpUpdate({
		sessionUpdate: "tool_call", toolCallId: "c", status: "pending",
		kind: "read" }).toolCall,
		{ tool_call_id: "c", status: "pending", kind: "read" });
});

test("W543: a supplied tool-call kind is copied, all ten of them", () => {
	assert.deepEqual([...TOOL_KINDS], ["read", "edit", "delete", "move",
		"search", "execute", "think", "fetch", "switch_mode", "other"]);
	for (const kind of TOOL_KINDS) {
		for (const sourceKind of ["tool_call", "tool_call_update"]) {
			assert.equal(normalizeAcpUpdate({ sessionUpdate: sourceKind,
				toolCallId: "c", status: "completed", kind }).toolCall.kind,
				kind, `${sourceKind}/${kind}`);
		}
	}
});

test("W543: an absent kind is OMITTED and is never invented", () => {
	// The captured trace's own shape — root-level id and status, no kind — is
	// now a positive example of the absent case rather than an undecidable
	// gap.
	const absent = normalizeAcpUpdate({ sessionUpdate: "tool_call",
		toolCallId: "tc-1", status: "in_progress" });
	assert.equal("kind" in absent.toolCall, false);
	// MIGRATED on the review's authority. `null` is the SDK's own "not
	// supplied" for an UPDATE, so it is absence there; the source used to be
	// `tool_call`, which does not admit null at all. The omission assertion
	// this case already made is unchanged.
	assert.equal("kind" in normalizeAcpUpdate({
		sessionUpdate: "tool_call_update", toolCallId: "c",
		status: "completed", kind: null }).toolCall, false);
	// AND NOTHING ELSE IN THE UPDATE MAY BE USED TO INFER ONE. A title, a
	// tool name, a command and a status are all present here and the member
	// is still absent: absence does not become `other`, which is the one
	// inference that would look most reasonable.
	const rich = normalizeAcpUpdate({ sessionUpdate: "tool_call",
		toolCallId: "c", status: "failed", title: "read a file",
		name: "fs_read", command: "cat /etc/passwd" });
	assert.equal("kind" in rich.toolCall, false);
	assert.equal(rich.toolCall.title, "read a file");
});

test("W543: a kind outside the pinned vocabulary REFUSES", () => {
	// A frozen contract is not widened by a provider sending a new word. A
	// later ACP vocabulary is explicit version/certification work.
	for (const invented of ["summon", "READ", "", "read ", "execute_command",
	                        7, true, ["read"]]) {
		assert.throws(() => normalizeAcpUpdate({ sessionUpdate: "tool_call",
			toolCallId: "c", status: "completed", kind: invented }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", String(invented));
	}
});

test("W543 review: null kind is absence only on a tool-call update", () => {
	assert.throws(() => normalizeAcpUpdate({ sessionUpdate: "tool_call",
		toolCallId: "c", status: "completed", kind: null }),
		(error) => error instanceof ContractError
			&& error.category === "integrity"
			&& error.code === "schema");
	assert.equal("kind" in normalizeAcpUpdate({
		sessionUpdate: "tool_call_update", toolCallId: "c",
		status: "completed", kind: null }).toolCall, false);
});

test("W543 review: an invalid kind always uses the closed error taxonomy", () => {
	assert.throws(() => normalizeAcpUpdate({ sessionUpdate: "tool_call",
		toolCallId: "c", status: "completed", kind: 1n }),
		(error) => error instanceof ContractError
			&& error.category === "integrity"
			&& error.code === "schema");
});

test("W543 correction: the source decides which shapes are absence", () => {
	// The failure this owns is not "null was handled wrongly" -- it is that
	// the SDK's declaration was QUOTED in the comment and then implemented on
	// one path. `kind?: ToolKind` on the initial call, `kind?: ToolKind |
	// null` on the update: three shapes, two sources, and the whole table is
	// the contract rather than the corner someone happened to test.
	const view = (sourceKind, fields) => normalizeAcpUpdate({
		sessionUpdate: sourceKind, toolCallId: "c", status: "completed",
		...fields }).toolCall;
	for (const [shape, fields, onCall, onUpdate] of [
			["an omitted member", {}, "absent", "absent"],
			["an explicit undefined", { kind: undefined }, "absent", "absent"],
			["an explicit null", { kind: null }, "refuses", "absent"],
			["a pinned value", { kind: "read" }, "read", "read"],
			["a value outside the ten", { kind: "summon" },
			 "refuses", "refuses"]]) {
		for (const [sourceKind, expected] of [["tool_call", onCall],
		                                      ["tool_call_update", onUpdate]]) {
			const what = `${shape} on ${sourceKind}`;
			if (expected === "refuses") {
				assert.throws(() => view(sourceKind, fields),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
			} else if (expected === "absent") {
				assert.equal("kind" in view(sourceKind, fields), false, what);
			} else {
				assert.equal(view(sourceKind, fields).kind, expected, what);
			}
		}
	}
});

test("W543 correction: a refusal names the shape and never runs the value", () => {
	// A diagnostic that serializes what it is rejecting hands the rejected
	// value control of the refusal. `JSON.stringify` did exactly that, and a
	// BigInt turned the closed pair into a raw TypeError.
	const hostile = {
		get toJSON() { throw new Error("toJSON was read"); },
		toString() { throw new Error("toString ran"); },
		valueOf() { throw new Error("valueOf ran"); },
	};
	const marker = "zz-not-a-tool-kind-zz";
	for (const [what, value] of [
			["a BigInt", 1n],
			["a symbol", Symbol("read")],
			// In the vocabulary BY VALUE and not by shape. The pinned type is
			// the string `read`, not an object that stringifies to it, and
			// membership is tested only after the shape is known.
			["a String object", new String("read")],
			["an object that throws if anything reads it", hostile],
			["a function", () => "read"],
			["an array", ["read"]],
			["a plain object", {}],
			["an invalid string", marker]]) {
		for (const sourceKind of ["tool_call", "tool_call_update"]) {
			assert.throws(() => normalizeAcpUpdate({ sessionUpdate: sourceKind,
				toolCallId: "c", status: "completed", kind: value }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema"
					// and the message describes the SHAPE rather than echoing
					// the value this boundary has just rejected.
					&& !error.message.includes(marker)
					&& error.message.includes(typeof value),
				`${what} on ${sourceKind}`);
		}
	}
});

test("W543: a kind survives sealing and decides nothing", () => {
	const store = open();
	try {
		withSession(store);
		const update = { sessionUpdate: "tool_call", toolCallId: "tc-1",
		                 status: "completed", kind: "execute" };
		const portable = normalizeAcpUpdate(update);
		const document = frame({ update });
		assert.deepEqual(document.tool_call, portable.toolCall);
		observeEvent(store, document);
		// It reached the durable frame through the frozen schema, which is
		// the half the old `additionalProperties: false` made impossible.
		assert.equal(eventRecordOf(store, REF, 1).document.tool_call.kind,
			"execute");
		// AND IT DECIDED NOTHING. The event's own kind comes from the §6.2
		// mapping, not from the tool kind, and no column carries it — the
		// ruling's "no permission, policy, tool authority, turn outcome or
		// disposition" is implemented by nothing reading it.
		const row = store.db.prepare(
			"SELECT kind, source_kind FROM agent_events").get();
		assert.equal(row.kind, "tool-call");
		assert.equal(row.source_kind, "tool_call");
	} finally {
		store.close();
	}
});

test("W2929 review: the captured ACP tool-call shape normalizes directly", () => {
	for (const sourceKind of ["tool_call", "tool_call_update"]) {
		const portable = normalizeAcpUpdate({ sessionUpdate: sourceKind,
			toolCallId: "provider-call-1", status: "in_progress",
			kind: "read" });
		assert.equal(portable.toolCall.tool_call_id, "provider-call-1",
			sourceKind);
		assert.equal(portable.toolCall.status, "in_progress", sourceKind);
	}
});

test("W2929 correction: the contentless kinds are the two the contract names",
	() => {
		// Held as a property so the set cannot quietly grow or shrink. Both
		// are diagnostics for the same reason from opposite directions:
		// `other` because nothing portable is known about the update, and
		// `agent-reasoning` because §6.2 says a chain of thought is never
		// portable evidence however well understood it is.
		for (const [sourceKind, kind] of [["user_message_chunk", "other"],
		                                  ["agent_thought_chunk",
		                                   "agent-reasoning"]]) {
			const portable = normalizeAcpUpdate({ sessionUpdate: sourceKind,
				content: [{ type: "text", text: "body" }] });
			assert.equal(portable.kind, kind);
			assert.deepEqual(portable.content, [], sourceKind);
			assert.equal(portable.byteCount > 0, true, sourceKind);
		}
		// And every OTHER mapped kind does carry admitted content, so the
		// exclusion is two rows rather than a general silence.
		for (const [sourceKind, kind] of Object.entries(ACP_SESSION_UPDATES)) {
			if (kind === "other" || kind === "agent-reasoning") continue;
			const update = { sessionUpdate: sourceKind,
			                 content: [{ type: "text", text: "body" }] };
			if (kind === "tool-call" || kind === "tool-call-update") {
				Object.assign(update, { toolCallId: "t", status: "pending" });
			}
			assert.deepEqual(normalizeAcpUpdate(update).content,
				[{ type: "text", text: "body" }], sourceKind);
		}
	});

// -- the seal covers the frame ----------------------------------------------

test("W2929: the sealed frame says nothing about having been observed", () => {
	const document = frame();
	// §6.4, and the reason is concrete: a retransmitted frame is the SAME
	// frame. Sealing lateness or the manager's ordering into it would make
	// one frame observed twice carry two digests, and an ordinary duplicate
	// indistinguishable from a spliced stream.
	assert.equal("late" in document, false);
	assert.equal("observation_seq" in document, false);
	const { document_digest: declared, ...rest } = document;
	assert.equal(declared, digest(rest), "the frame is not sealed over itself");
	assert.equal(document.redacted, true);
	assert.equal(document.turn_id, null);
});

test("W2929: a frame outside the closed kinds is refused before it is sealed",
	() => {
		assert.throws(() => frame({ kind: "agent-vibes" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
	});

test("W2929 re-review: a non-durable frame member reports a closed error",
	() => {
		assert.throws(() => frame({ adapterDiagnostics: {
			"baton.relay/1": { callback: () => "not JSON" } } }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
	});

test("W2929 correction: every durable member of the frame is OWNED or refused",
	() => {
		// The review drove diagnostics. These drive the other two members a
		// caller supplies, because the finding is that an interpreter
		// exception is not a closed pair — not that one field was missed.
		for (const [what, overrides] of [
				["content", { content: [{ type: "text",
				                          text: "x", clone: Symbol("no") }] }],
				["a tool call", { toolCall: { tool_call_id: "c",
				                              status: "pending",
				                              at: () => "not JSON" } }],
				["diagnostics", { adapterDiagnostics: {
					"baton.relay/1": { callback: () => "not JSON" } } }]]) {
			assert.throws(() => frame(overrides),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
		}
	});

test("W2929 correction: a precise canonical refusal is not flattened", () => {
	// An existing ContractError passes through unchanged. `Infinity` clones
	// perfectly well and fails at the CANONICAL boundary, which names the
	// rule exactly — a general "cannot own this" would have thrown that
	// precision away while reporting the same pair.
	assert.throws(() => frame({ adapterDiagnostics: {
		"baton.relay/1": { count: Infinity } } }),
		(error) => error instanceof ContractError
			&& error.category === "integrity"
			&& error.code === "schema"
			&& /infinity/.test(error.message)
			// UNCHANGED, not merely accurate: the canonical refusal must be
			// the one raised, not the general one with the precise text
			// interpolated into it. Interpolation would satisfy the pattern
			// above while a caller reading the first clause learned less.
			&& !/no canonical representation/.test(error.message));
});

test("W2929: a non-positive source sequence is refused by the SHAPE", () => {
	for (const sourceSeq of [0, -1, 1.5, "1", null]) {
		assert.throws(() => frame({ sourceSeq }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", String(sourceSeq));
	}
});

// -- observing one -----------------------------------------------------------

test("W2929: observing a frame records it and answers with the observation",
	() => {
		const store = open();
		try {
			withSession(store);
			const document = frame();
			const answer = observeEvent(store, document);
			// EXTENDED on the review's authority: §6.4 requires the consumer
			// to answer with the sealed bytes, so the exact answer carries
			// the document. Every metadata assertion is the one this case
			// already made.
			assert.deepEqual(answer, { sourceSeq: 1, observationSeq: 1,
				late: false, replayed: false,
				documentDigest: document.document_digest,
				document });
			const retained = eventRecordOf(store, REF, 1);
			assert.deepEqual(retained.document, document);
			assert.equal(retained.observationSeq, 1);
			assert.equal(retained.late, false);
			// The observation lives BESIDE the frame, in its own columns.
			const row = store.db.prepare(
				"SELECT observation_seq, late, kind, source_kind, byte_count "
				+ "FROM agent_events").get();
			assert.equal(row.observation_seq, 1);
			assert.equal(row.late, 0);
			assert.equal(row.kind, "agent-message");
			assert.equal(row.source_kind, "agent_message_chunk");
			assert.equal(row.byte_count, document.byte_count);
		} finally {
			store.close();
		}
	});

test("W2929 review: observation answers with the same owned sealed document",
	() => {
		const store = open();
		try {
			withSession(store);
			const document = frame();
			const first = observeEvent(store, document);
			assert.deepEqual(first.document, document,
				"§6.4 requires the consumer to answer with the sealed bytes");
			assert.notEqual(first.document, document,
				"the answer aliases the caller's submitted object");
			first.document.content[0].text = "caller edit";
			const replay = observeEvent(store, document);
			assert.deepEqual(replay.document, document,
				"replay did not return the durable sealed frame");
			assert.notEqual(replay.document, first.document,
				"two answers alias the same mutable object");
		} finally {
			store.close();
		}
	});

test("W2929: the manager's ordering advances per epoch and restarts with one",
	() => {
		const store = open();
		try {
			withSession(store);
			assert.equal(observeEvent(store, frame({ sourceSeq: 3 }))
				.observationSeq, 1, "the manager's ordering is not the relay's");
			assert.equal(observeEvent(store, frame({ sourceSeq: 1 }))
				.observationSeq, 2);
			// A NEW EPOCH restarts at one, and the epoch is part of the
			// identity so nothing collides.
			store.db.prepare(
				"UPDATE agent_sessions SET state = 'closed' WHERE "
				+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
				.run(ATTEMPT, REF.posture, REF.sessionEpoch);
			const later = withSession(store, { sessionEpoch: 2 });
			assert.equal(observeEvent(store,
				frame({ sessionRef: later, sourceSeq: 1 })).observationSeq, 1);
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM agent_events").get().n, 3);
		} finally {
			store.close();
		}
	});

test("W2929: the SAME frame replays its original observation", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame();
		const first = observeEvent(store, document);
		// Re-submitted from the caller's own object, mutated afterwards —
		// the answer must be the recorded one, not a fresh read of this.
		const again = observeEvent(store, { ...document });
		assert.deepEqual(again, { ...first, replayed: true });
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 1,
			"a duplicate was persisted twice");
	} finally {
		store.close();
	}
});

test("W2929 review: replay authenticates the retained sealed frame", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame();
		observeEvent(store, document);
		// A duplicate is an answer from durable state, not permission to trust
		// an index digest while returning the caller's retransmitted object.
		store.db.prepare(
			"UPDATE agent_events SET body = ? WHERE source_seq = 1")
			.run("not-json");
		assert.throws(() => observeEvent(store, document),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929: the same sequence with a DIFFERENT frame is an integrity failure",
	() => {
		const store = open();
		try {
			withSession(store);
			observeEvent(store, frame());
			// The transport lied about ordering or the stream was spliced,
			// and neither is a merge to attempt. Both sides are sealed, so
			// the two digests ARE the comparison.
			assert.throws(() => observeEvent(store, frame({
				update: { sessionUpdate: "agent_message_chunk",
				          content: [{ type: "text", text: "different" }] } })),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM agent_events").get().n, 1);
		} finally {
			store.close();
		}
	});

test("W2929: a frame naming another session is an identity mismatch", () => {
	const store = open();
	try {
		withSession(store, { providerSessionId: "provider-session-a" });
		assert.throws(() => observeEvent(store, frame({
			sessionRef: { ...REF, providerSessionId: "provider-session-b" } })),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "identity-mismatch");
		// And an omitted reference is not agreement either.
		assert.throws(() => observeEvent(store, frame()),
			(error) => error instanceof ContractError
				&& error.code === "identity-mismatch");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
		const agreeing = frame({
			sessionRef: { ...REF, providerSessionId: "provider-session-a" } });
		assert.equal(observeEvent(store, agreeing).observationSeq, 1);
	} finally {
		store.close();
	}
});

test("W2929 re-review: a retained read binds the full requested session",
	() => {
		const store = open();
		try {
			const exact = withSession(store,
				{ providerSessionId: "provider-session-a" });
			observeEvent(store, frame({ sessionRef: exact }));
			assert.throws(() => eventRecordOf(store,
				{ ...exact, providerSessionId: "provider-session-b" }, 1),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "identity-mismatch");
			assert.deepEqual(eventRecordOf(store, exact, 1).document
				.agent_session_ref.provider_session_id, "provider-session-a");
		} finally {
			store.close();
		}
	});

test("W2929 correction: absence and disagreement are different answers", () => {
	const store = open();
	try {
		const exact = withSession(store,
			{ providerSessionId: "provider-session-a" });
		observeEvent(store, frame({ sessionRef: exact }));
		// A sequence nobody observed is ABSENT.
		assert.equal(eventRecordOf(store, exact, 2), null);
		// So is an epoch that holds nothing, even though the attempt exists.
		assert.equal(eventRecordOf(store, { ...exact, sessionEpoch: 9 }, 1),
			null);
		// A PRESENT row whose sealed reference disagrees is a mismatch and
		// not an absence: answering null there would tell a caller no such
		// frame exists while the epoch holds one.
		const moved = { ...frame({ sessionRef: exact }) };
		delete moved.document_digest;
		const foreign = { ...moved,
			agent_session_ref: { ...moved.agent_session_ref,
			                     provider_session_id: "provider-session-b" } };
		const resealed = { ...foreign, document_digest: digest(foreign) };
		// Both halves moved together, so the seal agrees with itself and only
		// the reference the caller ASKED FOR does not.
		store.db.prepare(
			"UPDATE agent_events SET body = ?, document_digest = ? "
			+ "WHERE source_seq = 1")
			.run(canonicalBytes(resealed).toString("utf8"),
			     resealed.document_digest);
		assert.throws(() => eventRecordOf(store, exact, 1),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "identity-mismatch");
	} finally {
		store.close();
	}
});

test("W2929: an event happens INSIDE a session", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: PROFILE.document_digest });
		assert.throws(() => observeEvent(store, frame()),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

// -- lateness is decided once ------------------------------------------------

function endedTurn(store, token) {
	return recordTurn(store, { sessionRef: REF, turnToken: token,
		promptDigest: digest("prompt"), startedAt: NOW,
		deadlineAt: "2026-08-22T12:15:00.000Z",
		endedAt: "2026-08-22T12:01:00.000Z",
		terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
}

test("W2929: a frame arriving after its turn's terminal fact is marked late",
	() => {
		const store = open();
		try {
			withSession(store);
			const token = allocateTurn(store, REF).turnToken;
			endedTurn(store, token);
			const answer = observeEvent(store, frame({ turnId: token }),
				{ turnId: token });
			assert.equal(answer.late, true);
			// LATE, AND THAT IS ALL IT IS. §6.4: it never reopens the turn,
			// never changes the outcome, and never contributes to a
			// disposition — so the turn record is byte-identical afterwards.
			assert.equal(store.db.prepare(
				"SELECT outcome FROM turns WHERE turn_id = ?").get(token)
				.outcome, "completed");
			assert.equal(eventRecordOf(store, REF, 1).late, true);
		} finally {
			store.close();
		}
	});

test("W2929: lateness was decided when the frame was FIRST seen", () => {
	const store = open();
	try {
		withSession(store);
		const token = allocateTurn(store, REF).turnToken;
		const document = frame({ turnId: token });
		// Seen while the turn was still open, so it is not late.
		const first = observeEvent(store, document, { turnId: token });
		assert.equal(first.late, false);
		endedTurn(store, token);
		// The SAME frame, retransmitted after the terminal fact. A
		// retransmission is the same frame, so it replays the observation it
		// already has rather than acquiring a lateness it never had.
		const again = observeEvent(store, document, { turnId: token });
		assert.deepEqual(again, { ...first, replayed: true });
		assert.equal(eventRecordOf(store, REF, 1).late, false);
		// And a genuinely NEW frame after the same terminal fact is late,
		// which is what makes the answer above a replay rather than a bug.
		assert.equal(observeEvent(store,
			frame({ sourceSeq: 2, turnId: token }), { turnId: token }).late,
			true);
	} finally {
		store.close();
	}
});

test("W2929: a frame naming no turn is not late, whatever has ended", () => {
	const store = open();
	try {
		withSession(store);
		endedTurn(store, allocateTurn(store, REF).turnToken);
		// There is no terminal fact for it to be after: lateness is a
		// property of a frame's relationship to ITS turn.
		assert.equal(observeEvent(store, frame()).late, false);
	} finally {
		store.close();
	}
});

test("W2929: a frame cannot be observed into somebody else's turn", () => {
	const store = open();
	try {
		withSession(store);
		const token = allocateTurn(store, REF).turnToken;
		store.db.prepare(
			"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
			+ "session_epoch, profile_digest, pinned_policy, work_id, "
			+ "authority_uuid, state, opened_at) "
			+ "VALUES (?, 'consent', 1, ?, ?, ?, ?, 'ready', ?)")
			.run(ATTEMPT, PROFILE.document_digest, digest("policy"), WORK,
			     UUID, NOW);
		const foreign = allocateTurn(store, { ...REF, posture: "consent" })
			.turnToken;
		assert.throws(() => observeEvent(store, frame({ turnId: foreign }),
			{ turnId: foreign }),
			(error) => error instanceof ContractError
				&& error.code === "identity-mismatch");
		// And the frame's own turn must be the one it is observed into: a
		// sealed frame that names one turn and is filed under another is the
		// same disagreement seen from the other side.
		assert.throws(() => observeEvent(store, frame({ turnId: null }),
			{ turnId: token }),
			(error) => error instanceof ContractError
				&& error.code === "identity-mismatch");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: a sealed turn binding cannot disappear at observation",
	() => {
		const store = open();
		try {
			withSession(store);
			const document = frame({ turnId: "turn-not-allocated" });
			assert.throws(() => observeEvent(store, document),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "identity-mismatch");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
		} finally {
			store.close();
		}
	});

test("W2929 correction: a redundant turn operand may only AGREE", () => {
	const store = open();
	try {
		withSession(store);
		const token = allocateTurn(store, REF).turnToken;
		const other = allocateTurn(store, REF).turnToken;
		// Every disagreement, in both directions. The sealed frame decides;
		// an operand that says something else is not a hint to follow.
		for (const [what, document, options] of [
				["sealed null, operand named", frame({ turnId: null }),
				 { turnId: token }],
				["sealed named, operand null", frame({ turnId: token }),
				 { turnId: null }],
				["sealed named, operand different", frame({ turnId: token }),
				 { turnId: other }]]) {
			assert.throws(() => observeEvent(store, document, options),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "identity-mismatch", what);
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
		// Agreement, and the absence of an operand, both observe the SEALED
		// turn — which is the identity the durable row carries.
		assert.equal(observeEvent(store, frame({ turnId: token }),
			{ turnId: token }).sourceSeq, 1);
		assert.equal(observeEvent(store,
			frame({ sourceSeq: 2, turnId: token })).sourceSeq, 2);
		assert.deepEqual(store.db.prepare(
			"SELECT turn_id FROM agent_events ORDER BY source_seq")
			.all().map((row) => row.turn_id), [token, token]);
	} finally {
		store.close();
	}
});

// -- bounds, redaction and the retained frame --------------------------------

test("W2929: an over-limit frame is refused without partial action", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame({
			update: { sessionUpdate: "agent_message_chunk",
			          content: [{ type: "text", text: "x".repeat(2000) }] } });
		assert.equal(document.byte_count > PROFILE.limits.max_event_bytes, true);
		assert.throws(() => observeEvent(store, document),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "limit");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0,
			"an over-limit frame took partial action");
	} finally {
		store.close();
	}
});

test("W2929 review: the limit measures the sealed event, not its claimed count",
	() => {
		const store = open();
		try {
			withSession(store);
			const document = frame({
				update: { sessionUpdate: "agent_message_chunk",
					content: [{ type: "text",
					            text: "ordinary activity ".repeat(100) }] },
				byteCount: 1 });
			assert.equal(canonicalBytes(document).length
				> PROFILE.limits.max_event_bytes, true);
			assert.throws(() => observeEvent(store, document),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "limit");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
		} finally {
			store.close();
		}
	});

test("W2929 correction: byte_count keeps its own job and is not the bound", () => {
	const store = open();
	try {
		withSession(store);
		// The converse of the review's case. `byte_count` is SOURCE
		// accounting — it says how much update there was, including the parts
		// that were dropped — so a frame whose source was enormous and whose
		// normalized event is small is admitted, and the count survives.
		const document = frame({ byteCount: 10_000_000 });
		assert.equal(canonicalBytes(document).length
			< PROFILE.limits.max_event_bytes, true);
		assert.equal(observeEvent(store, document).sourceSeq, 1);
		assert.equal(store.db.prepare(
			"SELECT byte_count FROM agent_events").get().byte_count,
			10_000_000, "the source accounting was rewritten by the bound");
	} finally {
		store.close();
	}
});

test("W2929 correction: a replay refuses a retained frame that has drifted", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame();
		observeEvent(store, document);
		// Parsable, valid-shaped, and no longer what was sealed. The indexed
		// digest column still matches the incoming frame, so only reading the
		// record catches this.
		store.db.prepare(
			"UPDATE agent_events SET body = ? WHERE source_seq = 1")
			.run(JSON.stringify({ ...document, byte_count: 99 }));
		assert.throws(() => observeEvent(store, document),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929: the bound comes from the profile the session actually opened under",
	() => {
		const store = open();
		try {
			withSession(store);
			// A bound nobody can read is not a bound: withdrawing the profile
			// must refuse rather than silently fall back to some default.
			store.db.prepare(
				"UPDATE profiles SET withdrawn_at = ? WHERE digest = ?")
				.run(NOW, PROFILE.document_digest);
			assert.throws(() => observeEvent(store, frame()),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
		} finally {
			store.close();
		}
	});

test("W2929: a bearer ANYWHERE in the frame is refused", () => {
	const store = open();
	try {
		withSession(store);
		for (const [what, overrides] of [
				["text content", { update: {
					sessionUpdate: "agent_message_chunk",
					content: [{ type: "text",
					            text: `the token is ${GOLDEN_BEARER}` }] } }],
				["a resource link", { update: {
					sessionUpdate: "agent_message_chunk",
					content: [{ type: "resource_link",
					            uri: `file:///w/${GOLDEN_BEARER}`,
					            name: "a" }] } }],
				["a nested diagnostic", {
					adapterDiagnostics: { "baton.relay/1": {
						nested: { deep: GOLDEN_BEARER } } } }]]) {
			assert.throws(() => observeEvent(store, frame(overrides)),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "secret-leak", what);
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: the seal is checked BEFORE any other field is read", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame();
		// A frame whose bytes moved after sealing. Its identity, sequence and
		// kind are all still perfectly good — and none of them get a hearing,
		// because a frame whose digest was never checked has no claim on any
		// rule that follows.
		assert.throws(() => observeEvent(store,
			{ ...document, byte_count: document.byte_count + 1 }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM agent_events").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: the retained frame survives byte for byte and re-binds", () => {
	const store = open();
	try {
		withSession(store);
		const document = frame({ adapterDiagnostics: {
			"baton.relay/1": { note: "x" } } });
		observeEvent(store, document);
		assert.equal(store.db.prepare(
			"SELECT body FROM agent_events").get().body,
			canonicalBytes(document).toString("utf8"));
		assert.equal(eventRecordOf(store, REF, 2), null,
			"a sequence nobody observed answered with a record");
		// A hand edit is caught on the way out, as it is for turns, profiles
		// and manifests.
		store.db.prepare("UPDATE agent_events SET body = ? WHERE source_seq = 1")
			.run(JSON.stringify({ ...document, byte_count: 99 }));
		assert.throws(() => eventRecordOf(store, REF, 1),
			(error) => error instanceof ContractError
				&& error.code === "digest");
		// And bytes that cannot be parsed at all report the same closed pair
		// rather than whichever error the parser reached first.
		store.db.prepare("UPDATE agent_events SET body = ? WHERE source_seq = 1")
			.run("not-json");
		assert.throws(() => eventRecordOf(store, REF, 1),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929: a frame filed under another sequence is refused", () => {
	const store = open();
	try {
		withSession(store);
		const first = frame({ sourceSeq: 1 });
		const other = frame({ sourceSeq: 2 });
		observeEvent(store, first);
		observeEvent(store, other);
		// Both halves moved together, so every digest still agrees — only the
		// sequence the caller ASKED FOR does not.
		store.db.prepare(
			"UPDATE agent_events SET body = ?, document_digest = ? "
			+ "WHERE source_seq = 1")
			.run(canonicalBytes(other).toString("utf8"),
			     other.document_digest);
		assert.throws(() => eventRecordOf(store, REF, 1),
			(error) => error instanceof ContractError
				&& error.code === "digest"
				&& /calls itself/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: the frozen session-state vocabulary is what this suite drove", () => {
	// The event boundary deliberately does not gate on session state: §6.4
	// gives it identity, sequence and lateness rules and no state rule, and
	// inventing one here would be this module deciding a question §7.3 owns.
	// Asserted so the omission is a recorded decision rather than a gap.
	assert.equal(SESSION_STATES.includes("ready"), true);
	assert.equal(SESSION_STATES.includes("closed"), true);
});
