// W2929 item 4, fifth slice: the handshake and the closed surface.
//
// The sets here belong to the VERSION, so most of these cases are about a
// profile being unable to widen them and about the relay refusing a surface
// whether or not the agent offers it.
//
// AND THEY ARE DRIVEN AGAINST THE FROZEN MODEL'S OWN LITERALS. The first
// event review caught me building against §6.2's prose while the captured
// trace said something else, and my fixture agreed with my code because I
// wrote both. So the four sets are parsed out of
// `evidence/acp_boundary_model.py` and compared, rather than retyped here
// where a shared typo would be invisible.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { certifyAgentSessionProfile }
	from "../src/worker_manager/agent_profile.mjs";
import { ACP_CLIENT_CAPABILITY_MEMBERS, ACP_UNSTABLE_CLIENT_CAPABILITIES,
         ACP_CLIENT_CAPABILITIES, AGENT_ORIGIN_METHODS,
         CAPABILITY_CLIENT_METHODS, RELAY_OUTBOUND_SURFACE,
         OPTIONAL_AGENT_METHODS,
         REFUSED_AGENT_METHODS, REQUIRED_AGENT_METHODS,
         REQUIRED_METHODS_BY_WIRE, SESSION_CAPABILITIES, bindProvider,
         checkOutboundMethod, negotiateAcp, routeAgentOriginCall,
         serveClientMethod, validateClientCapabilities }
	from "../src/worker_manager/agent_handshake.mjs";

after(removeOwnedRoots);

const NOW = "2026-08-22T12:00:00.000Z";
const HERE = dirname(fileURLToPath(import.meta.url));
const MODEL = readFileSync(join(HERE, "..", "..", "work", "records", "2026",
	"08", "finding-v12-isolated-agent-workers", "findings",
	"finding-v12-worker-contract", "findings", "finding-acp-agent-boundary",
	"evidence", "acp_boundary_model.py")).toString("utf8");

/** The string members of one `frozenset({...})` or tuple in the model. */
function modelSet(name) {
	const at = MODEL.indexOf(`${name} = `);
	assert.notEqual(at, -1, `${name} is not in the frozen model`);
	const opened = MODEL.indexOf("(", at);
	let depth = 0;
	let end = opened;
	for (; end < MODEL.length; end += 1) {
		if (MODEL[end] === "(") depth += 1;
		if (MODEL[end] === ")") {
			depth -= 1;
			if (depth === 0) break;
		}
	}
	const body = MODEL.slice(opened, end);
	return [...body.matchAll(/"([^"]+)"/g)].map((match) => match[1]).sort();
}

const ACP_PROFILE = (() => {
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "profile",
		profile_id: "profile-handshake-acp",
		created_at: NOW,
		wire_protocol: "acp",
		pinned_wire_version: 1,
		provider_binding: null,
		adapter: { name: "native-acp-relay", version: "1.0-test",
		           build_digest: digest("adapter") },
		client_capabilities: { fs: {}, terminal: false },
		session_capabilities: [...SESSION_CAPABILITIES].sort(),
		postures: {
			consent: { policy: { kind: "acp", session_mode_id: "plan" },
			           workspace: false, declared_output: false },
			execution: { policy: { kind: "acp",
			                       session_mode_id: "acceptEdits" },
			             workspace: true, declared_output: true },
		},
		mcp_servers: [],
		limits: { setup_deadline_ms: 120000, turn_deadline_ms: 900000,
		          cancel_drain_deadline_ms: 30000, max_event_bytes: 16000,
		          max_queue_events: 1024, max_queue_bytes: 4194304 },
		agent_policy_digest: digest("policy"),
	};
	return { ...body, document_digest: digest(body) };
})();

const BUILD = "codex-cli-0.149.0";
const INTERFACE = digest("interface");

function codexProfile(overrides = {}) {
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "profile",
		profile_id: "profile-handshake-codex",
		created_at: NOW,
		wire_protocol: "codex-app-server",
		pinned_wire_version: null,
		provider_binding: { provider: "codex-app-server",
			server_build_id: BUILD, interface_digest: INTERFACE,
			certified_at: NOW, experimental_api: false, ...overrides },
		adapter: { name: "codex-app-server-adapter", version: "1.0-test",
		           build_digest: digest("codex-adapter") },
		client_capabilities: null,
		session_capabilities: [...SESSION_CAPABILITIES].sort(),
		postures: {
			consent: { policy: { kind: "codex-app-server",
				thread_start: { approval_policy: "never", sandbox: "readOnly",
				                cwd_role: "scratch", model: "gpt-5-codex" },
				turn_start: { approval_policy: "never",
				              sandbox_policy: { type: "readOnly" },
				              cwd_role: "scratch", model: "gpt-5-codex" } },
			           workspace: false, declared_output: false },
			execution: { policy: { kind: "codex-app-server",
				thread_start: { approval_policy: "never",
				                sandbox: "workspaceWrite",
				                cwd_role: "workspace", model: "gpt-5-codex" },
				turn_start: { approval_policy: "never",
				              sandbox_policy: { type: "workspaceWrite",
				                                network_access: false },
				              cwd_role: "workspace", model: "gpt-5-codex" } },
			             workspace: true, declared_output: true },
		},
		mcp_servers: [],
		limits: { setup_deadline_ms: 120000, turn_deadline_ms: 900000,
		          cancel_drain_deadline_ms: 30000, max_event_bytes: 16000,
		          max_queue_events: 1024, max_queue_bytes: 4194304 },
		agent_policy_digest: digest("policy"),
	};
	return { ...body, document_digest: digest(body) };
}

function open(profiles = [ACP_PROFILE]) {
	const store = new ControlStore(
		join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
	for (const profile of profiles) certifyAgentSessionProfile(store, profile);
	return store;
}

const OFFERED = {
	agentProtocolVersion: 1,
	agentMethods: [...REQUIRED_AGENT_METHODS, "session/set_mode"],
	agentSessionCapabilities: [...SESSION_CAPABILITIES],
};

// -- the sets belong to the version ------------------------------------------

test("W2929: the closed sets are the frozen model's, member for member", () => {
	// Compared against the design model rather than retyped, because a set I
	// transcribe twice is a set I can get wrong twice in the same direction.
	assert.deepEqual([...REQUIRED_AGENT_METHODS].sort(),
		modelSet("REQUIRED_AGENT_METHODS"));
	assert.deepEqual([...REFUSED_AGENT_METHODS].sort(),
		modelSet("REFUSED_AGENT_METHODS"));
	assert.deepEqual([...CAPABILITY_CLIENT_METHODS].sort(),
		modelSet("CAPABILITY_CLIENT_METHODS"));
	assert.deepEqual([...SESSION_CAPABILITIES].sort(),
		modelSet("SESSION_CAPABILITIES"));
	assert.deepEqual([...ACP_CLIENT_CAPABILITY_MEMBERS].sort(),
		modelSet("ACP_CLIENT_CAPABILITY_MEMBERS"));
	assert.deepEqual([...ACP_UNSTABLE_CLIENT_CAPABILITIES].sort(),
		modelSet("ACP_UNSTABLE_CLIENT_CAPABILITIES"));
	// Five required, six capabilities, and the refused list is not empty —
	// stated so a set emptied by a bad edit fails here rather than passing
	// every membership case vacuously.
	assert.equal(REQUIRED_AGENT_METHODS.length, 5);
	assert.equal(SESSION_CAPABILITIES.length, 6);
	assert.equal(REFUSED_AGENT_METHODS.length > 0, true);
});

test("W2929: required and refused never overlap, and each wire has its own", () => {
	assert.deepEqual(REQUIRED_AGENT_METHODS
		.filter((method) => REFUSED_AGENT_METHODS.includes(method)), [],
		"a method is both required and refused");
	assert.deepEqual(REQUIRED_AGENT_METHODS
		.filter((method) => CAPABILITY_CLIENT_METHODS.includes(method)), [],
		"an agent method is also a served client method");
	// "Required" is a property of the WIRE. The Codex App Server presents
	// four methods of its own and none of ACP's five.
	assert.deepEqual([...REQUIRED_METHODS_BY_WIRE["codex-app-server"]],
		["initialize", "thread/start", "turn/start", "turn/interrupt"]);
	assert.equal(REQUIRED_METHODS_BY_WIRE.acp, REQUIRED_AGENT_METHODS);
});

test("W2929: the relay advertises nothing, and `session` is stable and absent",
	() => {
		// SUPERSEDED under W641's ruling. The previous round asserted TWO
		// documents and that they DIFFERED; W641 ruled the normalized summary
		// is the contract defect rather than a second shape to name, so there
		// is one document and the profile persists it. The withholding
		// assertions below are the ones this case has always made.
		assert.deepEqual(ACP_CLIENT_CAPABILITIES, { fs: {}, terminal: false });
		assert.deepEqual(Object.keys(ACP_CLIENT_CAPABILITIES.fs), [],
			"withholding is expressed by absence, so fs is empty");
		// And the certified profile persists the SAME structural document.
		assert.deepEqual(ACP_PROFILE.client_capabilities,
			ACP_CLIENT_CAPABILITIES);
		// §2.2 withholds EVERYTHING rather than everything unsafe: `session`
		// is stable, is not in the unstable set, and is still not advertised.
		assert.equal(ACP_CLIENT_CAPABILITY_MEMBERS.includes("session"), true);
		assert.equal(ACP_UNSTABLE_CLIENT_CAPABILITIES.includes("session"),
			false);
		for (const member of ACP_CLIENT_CAPABILITY_MEMBERS) {
			if (member === "fs" || member === "terminal") continue;
			assert.equal(member in ACP_CLIENT_CAPABILITIES, false,
				member);
		}
	});

test("W2929: an advertisement that is not EXACTLY the minimal one is denied",
	() => {
		validateClientCapabilities(structuredClone(
			ACP_CLIENT_CAPABILITIES));
		for (const [what, offered] of [
				["a readable filesystem", { fs: { readTextFile: true },
					terminal: false }],
				// Present at all, even set FALSE: the wire withholds by
				// absence, and this boundary is where that difference is
				// still visible.
				["a filesystem member set false", { fs: { readTextFile: false },
					terminal: false }],
				// The shape the frozen schema used to REQUIRE. W641 removed
				// it, so it is a refused transport member like any other.
				["the removed summary's shape", { fs: { read_text_file: false,
					write_text_file: false }, terminal: false }],
				["a terminal", { fs: {}, terminal: true }],
				// A member ACP adds next version passes a subset check on the
				// day it appears, which is why the comparison is exact.
				["a new stable member", { ...ACP_CLIENT_CAPABILITIES,
					session: {} }],
				["an unstable member", { ...ACP_CLIENT_CAPABILITIES,
					elicitation: true }],
				["nothing at all", {}],
				["fs missing", { terminal: false }],
				["an array", []],
				["absent", undefined]]) {
			assert.throws(() => validateClientCapabilities(offered),
				(error) => error instanceof ContractError
					&& error.category === "policy"
					&& error.code === "denied", what);
		}
	});

test("W641: the profile persists the SAME document the relay sends", () => {
	// SUPERSEDED under W641's ruling and inverted by it. This case used to
	// assert that the profile's durable summary was REFUSED as an
	// advertisement — because the two representations differed. The ruling
	// removed the summary, so the profile's own document is now exactly what
	// the relay sends and validates, and the case asserts that instead.
	const wire = { fs: {}, terminal: false };
	assert.deepEqual(ACP_PROFILE.client_capabilities, wire);
	assert.doesNotThrow(() => validateClientCapabilities(wire));
	assert.doesNotThrow(
		() => validateClientCapabilities(ACP_PROFILE.client_capabilities));
	const store = open();
	try {
		const negotiated = negotiateAcp(store, ACP_PROFILE.document_digest,
			OFFERED);
		assert.deepEqual(negotiated.clientCapabilities, wire);
		// An OWNED copy: one representation is not one object.
		assert.notEqual(negotiated.clientCapabilities,
			ACP_PROFILE.client_capabilities);
		assert.notEqual(negotiated.clientCapabilities,
			ACP_CLIENT_CAPABILITIES);
	} finally {
		store.close();
	}
});

test("W2929 review: exact capability equality is structural, not key order",
	() => {
		// JSON object member order carries no meaning. An exact boundary
		// rejects a different member or value, not the same object serialized
		// in a different insertion order.
		assert.doesNotThrow(() => validateClientCapabilities(
			{ terminal: false, fs: {} }));
	});

test("W641 review: structural equality is equality of JSON documents", () => {
	// `Object.keys(new Date(0))` is empty, but the value serializes as a STRING,
	// not `{}`. Treating every object with no enumerable members as the empty
	// ACP document admits a different wire shape through the exact boundary.
	assert.throws(() => validateClientCapabilities(
		{ fs: new Date(0), terminal: false }),
		(error) => error instanceof ContractError
			&& error.category === "policy"
			&& error.code === "denied");
	// A null-prototype record is still an inert JSON object and must remain a
	// valid spelling of the same structural document.
	const fs = Object.create(null);
	const document = Object.create(null);
	document.terminal = false;
	document.fs = fs;
	assert.doesNotThrow(() => validateClientCapabilities(document));
});

test("W641 review: an unsupported value keeps the closed refusal taxonomy",
	() => {
	// The boundary has already decided this is not `false`; formatting the
	// rejected value must not replace policy.denied with JSON.stringify's raw
	// BigInt TypeError.
	assert.throws(() => validateClientCapabilities({ fs: {}, terminal: 1n }),
		(error) => error instanceof ContractError
			&& error.category === "policy"
			&& error.code === "denied");
	});

test("W641 correction: an inert JSON record is proved at BOTH levels", () => {
	// The review found the Date at `fs`. The rule is that §2.2's document is
	// a document at every level of it, so each shape below is offered as the
	// whole envelope AND as `fs`.
	class Own {}
	const denied = (error) => error instanceof ContractError
		&& error.category === "policy" && error.code === "denied";
	const revoked = () => {
		const pair = Proxy.revocable({}, {});
		pair.revoke();
		return pair.proxy;
	};
	for (const [what, make] of [
			["a Date", () => new Date(0)],
			["a Map", () => new Map()],
			["a regular expression", () => /x/],
			["a class instance", () => new Own()],
			["an array", () => []],
			// Array classification follows a Proxy to its target; the
			// prototype trap answers whatever it likes.
			["an array wearing Object.prototype",
			 () => new Proxy([], { getPrototypeOf: () => Object.prototype })],
			["a revoked Proxy", revoked],
			["a bigint", () => 1n],
			["null", () => null],
			["a string", () => "{}"]]) {
		assert.throws(() => validateClientCapabilities(make()), denied,
			`${what} as the envelope`);
		assert.throws(() => validateClientCapabilities(
			{ fs: make(), terminal: false }), denied, `${what} as fs`);
	}
	// The two spellings §2.2 DOES send survive, at both levels and in either
	// insertion order.
	const nullProto = () => Object.create(null);
	assert.doesNotThrow(() => validateClientCapabilities(
		{ fs: nullProto(), terminal: false }));
	const reversed = nullProto();
	reversed.terminal = false;
	reversed.fs = {};
	assert.doesNotThrow(() => validateClientCapabilities(reversed));
});

test("W641 correction: a document carries DATA, seen and unseen", () => {
	const denied = (error) => error instanceof ContractError
		&& error.category === "policy" && error.code === "denied";
	let ran = false;
	// `Object.keys` does not show a non-enumerable member, and a
	// non-enumerable `toJSON` decides the ENTIRE wire form of the document
	// it hides in. Looking empty is not being the empty document.
	const hiding = (base) => {
		const value = { ...base };
		Object.defineProperty(value, "toJSON", {
			value: () => "not a document", enumerable: false });
		return value;
	};
	assert.throws(() => validateClientCapabilities(
		hiding({ fs: {}, terminal: false })), denied, "a hidden toJSON");
	assert.throws(() => validateClientCapabilities(
		{ fs: hiding({}), terminal: false }), denied, "fs hiding a toJSON");
	// A document may also refuse to say what its members ARE. This proxy
	// answers Object.prototype and exactly [fs, terminal] and then throws
	// from the descriptor trap — the one reflection that happens AFTER the
	// record has otherwise been proved, and the last place a rejected value
	// can still escape the closed pair.
	assert.throws(() => validateClientCapabilities(new Proxy({}, {
		getPrototypeOf: () => Object.prototype,
		ownKeys: () => ["fs", "terminal"],
		getOwnPropertyDescriptor() { throw new Error("descriptor trap"); },
	})), denied, "a document that refuses to describe its members");
	// And a member that is a PROGRAM is refused without being run: a getter
	// may answer one thing to the check and another to the wire.
	for (const [what, offered] of [
			["fs as an accessor", (() => {
				const value = { terminal: false };
				Object.defineProperty(value, "fs", {
					get() { ran = true; return {}; }, enumerable: true });
				return value;
			})()],
			["terminal as an accessor", (() => {
				const value = { fs: {} };
				Object.defineProperty(value, "terminal", {
					get() { ran = true; return false; }, enumerable: true });
				return value;
			})()]]) {
		ran = false;
		assert.throws(() => validateClientCapabilities(offered), denied, what);
		assert.equal(ran, false, `${what}: the getter ran`);
	}
});

test("W641 second review: a Proxy envelope is behavior, not a document",
	() => {
		const denied = (error) => error instanceof ContractError
			&& error.category === "policy" && error.code === "denied";
		let ran = false;
		const target = { fs: {}, terminal: false };
		const offered = new Proxy(target, {
			getPrototypeOf() { ran = true; return Object.prototype; },
			ownKeys() { ran = true; return Reflect.ownKeys(target); },
			getOwnPropertyDescriptor(_target, name) {
				ran = true;
				return Reflect.getOwnPropertyDescriptor(target, name);
			},
			get(_target, name) { ran = true; return Reflect.get(target, name); },
		});
		assert.throws(() => validateClientCapabilities(offered), denied);
		assert.equal(ran, false, "proving the envelope ran caller code");
	});

test("W641 second review: a Proxy fs is behavior, not a document", () => {
	const denied = (error) => error instanceof ContractError
		&& error.category === "policy" && error.code === "denied";
	let ran = false;
	const target = {};
	const fs = new Proxy(target, {
		getPrototypeOf() { ran = true; return Object.prototype; },
		ownKeys() { ran = true; return Reflect.ownKeys(target); },
	});
	assert.throws(() => validateClientCapabilities({ fs, terminal: false }),
		denied);
	assert.equal(ran, false, "proving fs ran caller code");
});

test("W641 third review: hidden fields are not the wire document", () => {
	const offered = {};
	Object.defineProperties(offered, {
		fs: { value: {}, enumerable: false },
		terminal: { value: false, enumerable: false },
	});
	assert.equal(JSON.stringify(offered), "{}",
		"the offered document omits both required wire fields");
	assert.throws(() => validateClientCapabilities(offered),
		(error) => error instanceof ContractError
			&& error.category === "policy" && error.code === "denied");
});

test("W641 correction: no refusal serializes what it refuses, at any site", () => {
	// The review found `JSON.stringify` on `terminal`. The envelope and `fs`
	// sites carried the same line and the same defect: a rule applied at one
	// of three sites is not applied.
	let ran = false;
	const hostile = () => {
		const value = {};
		for (const member of ["toJSON", "toString", "valueOf"]) {
			Object.defineProperty(value, member, {
				get() { ran = true; throw new Error(`${member} was read`); },
				enumerable: true });
		}
		return value;
	};
	// A revoked Proxy is not hostile so much as ABSENT: every reflection on it
	// throws, including `Array.isArray`, which follows a proxy to its target.
	// `terminal` is the one member whose value is described rather than
	// structurally proved, so it is the site where that reaches a diagnostic.
	const revoked = () => {
		const pair = Proxy.revocable({}, {});
		pair.revoke();
		return pair.proxy;
	};
	for (const [what, offered] of [
			["the envelope", 1n],
			["fs", { fs: 1n, terminal: false }],
			["terminal", { fs: {}, terminal: 1n }],
			["a hostile envelope", hostile()],
			["a hostile fs", { fs: hostile(), terminal: false }],
			["a hostile terminal", { fs: {}, terminal: hostile() }],
			["a revoked terminal", { fs: {}, terminal: revoked() }]]) {
		ran = false;
		assert.throws(() => validateClientCapabilities(offered),
			(error) => error instanceof ContractError
				&& error.category === "policy"
				&& error.code === "denied", what);
		assert.equal(ran, false, `${what}: the refusal read the value`);
	}
});

// -- ACP negotiation ---------------------------------------------------------

test("W2929: an exact wire version negotiates, and nothing else does", () => {
	const store = open();
	try {
		const negotiated = negotiateAcp(store, ACP_PROFILE.document_digest,
			OFFERED);
		// MIGRATED on the review's authority: the relay SENDS the wire
		// document. The fresh-copy assertion below is unchanged.
		assert.deepEqual(negotiated, {
			wireVersion: 1,
			clientCapabilities: { fs: {}, terminal: false },
			sessionCapabilities: [...SESSION_CAPABILITIES].sort() });
		// The answer is OWNED: editing it must not reach the module constant
		// the next handshake will return.
		negotiated.clientCapabilities.terminal = true;
		negotiated.sessionCapabilities.push("session.reuse");
		assert.equal(ACP_CLIENT_CAPABILITIES.terminal, false);
		assert.equal(SESSION_CAPABILITIES.includes("session.reuse"), false);
		// NO DOWNGRADE, and no upgrade either: an answer is an announcement,
		// and the profile pinned the version this manager certified against.
		for (const version of [0, 2, "1", null, undefined]) {
			assert.throws(() => negotiateAcp(store, ACP_PROFILE.document_digest,
				{ ...OFFERED, agentProtocolVersion: version }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "unsupported-version", String(version));
		}
	} finally {
		store.close();
	}
});

test("W2929: every required method is required, one at a time", () => {
	const store = open();
	try {
		// EXHAUSTIVE: a missing-method check tested on one member is a check
		// nobody has driven.
		for (const missing of REQUIRED_AGENT_METHODS) {
			const offered = OFFERED.agentMethods
				.filter((method) => method !== missing);
			assert.throws(() => negotiateAcp(store, ACP_PROFILE.document_digest,
				{ ...OFFERED, agentMethods: offered }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "capability"
					&& error.message.includes(missing), missing);
		}
		for (const [what, agentMethods] of [["none", []],
		                                    ["not a list", "initialize"],
		                                    ["absent", undefined]]) {
			assert.throws(() => negotiateAcp(store, ACP_PROFILE.document_digest,
				{ ...OFFERED, agentMethods }),
				(error) => error instanceof ContractError
					&& error.code === "capability", what);
		}
	} finally {
		store.close();
	}
});

test("W2929: all six session capabilities are mandatory, one at a time", () => {
	const store = open();
	try {
		for (const missing of SESSION_CAPABILITIES) {
			const offered = SESSION_CAPABILITIES
				.filter((capability) => capability !== missing);
			assert.throws(() => negotiateAcp(store, ACP_PROFILE.document_digest,
				{ ...OFFERED, agentSessionCapabilities: offered }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "capability"
					&& error.message.includes(missing), missing);
		}
		// And an agent offering a seventh gains nothing: `session.reuse`
		// deliberately does not exist, so it is neither required nor honoured.
		const negotiated = negotiateAcp(store, ACP_PROFILE.document_digest,
			{ ...OFFERED, agentSessionCapabilities:
				[...SESSION_CAPABILITIES, "session.reuse"] });
		assert.deepEqual(negotiated.sessionCapabilities,
			[...SESSION_CAPABILITIES].sort());
	} finally {
		store.close();
	}
});

test("W2929: a handshake is conducted under a CERTIFIED profile or not at all",
	() => {
		const store = open();
		try {
			assert.throws(() => negotiateAcp(store, digest("never certified"),
				OFFERED),
				(error) => error instanceof ContractError
					&& error.category === "policy"
					&& error.code === "profile-uncertified");
			// Withdrawal is not a document edit and it is not invisible here:
			// a profile that was certified and is not now certifies nothing.
			store.db.prepare(
				"UPDATE profiles SET withdrawn_at = ? WHERE digest = ?")
				.run(NOW, ACP_PROFILE.document_digest);
			assert.throws(() => negotiateAcp(store,
				ACP_PROFILE.document_digest, OFFERED),
				(error) => error instanceof ContractError
					&& error.code === "profile-uncertified");
		} finally {
			store.close();
		}
	});

// -- provider binding replaces negotiation, and neither reaches the other ----

test("W2929: a provider with no wire version is certified by its BUILD", () => {
	const profile = codexProfile();
	const store = open([ACP_PROFILE, profile]);
	try {
		const bound = bindProvider(store, profile.document_digest,
			{ observedBuildId: BUILD, observedInterfaceDigest: INTERFACE });
		assert.equal(bound.wireVersion, null);
		assert.equal(bound.providerBinding.server_build_id, BUILD);
		// OWNED, like the negotiated answer.
		bound.providerBinding.server_build_id = "edited";
		assert.equal(bindProvider(store, profile.document_digest,
			{ observedBuildId: BUILD, observedInterfaceDigest: INTERFACE })
			.providerBinding.server_build_id, BUILD);
		for (const [what, observed] of [
				["a different build", { observedBuildId: "codex-cli-0.150.0",
					observedInterfaceDigest: INTERFACE }],
				["a drifted interface", { observedBuildId: BUILD,
					observedInterfaceDigest: digest("moved") }],
				["nothing observed", {}]]) {
			assert.throws(() => bindProvider(store, profile.document_digest,
				observed),
				(error) => error instanceof ContractError
					&& error.category === "policy"
					&& error.code === "profile-uncertified", what);
		}
	} finally {
		store.close();
	}
});

test("W2929: a profile enabling the experimental API cannot be certified",
	() => {
		// §2.5 makes every unstable surface adapter-private diagnostic
		// material, so certifying it on would be certifying exactly the
		// surface that may never reach a portable state. The frozen schema
		// makes `experimental_api` a CONSTANT false, so the refusal lands at
		// certification — the earliest boundary there is, and the reason
		// `bindProvider`'s own check is measured rather than counted.
		const profile = codexProfile({ experimental_api: true });
		const store = new ControlStore(
			join(ownedTemp("v12-manager-"), "control.sqlite3"),
			{ incarnation: "manager-1", clock: () => NOW });
		try {
			assert.throws(() => certifyAgentSessionProfile(store, profile),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			// And a handshake against it therefore finds nothing certified,
			// which is the same refusal a withdrawn profile gets.
			assert.throws(() => bindProvider(store, profile.document_digest,
				{ observedBuildId: BUILD,
				  observedInterfaceDigest: INTERFACE }),
				(error) => error instanceof ContractError
					&& error.category === "policy"
					&& error.code === "profile-uncertified");
		} finally {
			store.close();
		}
	});

test("W2929: negotiation and binding refuse each other's profiles", () => {
	const profile = codexProfile();
	const store = open([ACP_PROFILE, profile]);
	try {
		// Binding REPLACES negotiation; it is not a second spelling of it, so
		// neither door opens for the other's document.
		//
		// The agent answers `null`, which is exactly what this profile pins,
		// so the version comparison AGREES and only the wire-protocol check
		// can refuse. Offering `1` here would have been refused by the
		// version rule with the same pair for a different reason, and the
		// case would have proved nothing about the door it names.
		assert.throws(() => negotiateAcp(store, profile.document_digest,
			{ ...OFFERED, agentProtocolVersion: null }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "unsupported-version"
				&& /negotiation belongs to ACP/.test(error.message));
		assert.throws(() => bindProvider(store, ACP_PROFILE.document_digest,
			{ observedBuildId: BUILD, observedInterfaceDigest: INTERFACE }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "unsupported-version");
	} finally {
		store.close();
	}
});

// -- the surface is refused whether or not it is offered ---------------------

test("W2929: the relay never SENDS a refused method, all twenty-one", () => {
	// Exhaustive over the frozen list, because a refusal list checked at
	// three of twenty-one points is a list nobody has checked.
	for (const method of REFUSED_AGENT_METHODS) {
		assert.throws(() => checkOutboundMethod(method),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "capability", method);
	}
	// MIGRATED on the review's authority, and RENAMED so the direction is in
	// the name. The handshake requirement is still five; the relay-OUTBOUND
	// surface is the four the relay originates plus the three optional ones,
	// because `session/update` is a notification the AGENT sends.
	assert.equal(REQUIRED_AGENT_METHODS.length, 5);
	assert.deepEqual([...OPTIONAL_AGENT_METHODS], ["session/set_mode",
		"session/set_config_option", "session/close"]);
	assert.deepEqual([...RELAY_OUTBOUND_SURFACE], ["initialize", "session/new",
		"session/prompt", "session/cancel", "session/set_mode",
		"session/set_config_option", "session/close"]);
	assert.equal(RELAY_OUTBOUND_SURFACE.length, 7);
	// EXHAUSTIVE pass-through over the seven, which is the assertion this
	// case already made over the set it then had.
	for (const method of RELAY_OUTBOUND_SURFACE) {
		assert.equal(checkOutboundMethod(method), method);
	}
	// AN ALLOW LIST, so the twenty-one enumerated refusals are not the rule —
	// they are twenty-one names that happen to be outside it. A method the
	// contract has never heard of is refused for the same reason.
	for (const method of ["session/reuse", "vendor/future_method", "", null,
	                      undefined, "SESSION/PROMPT"]) {
		assert.throws(() => checkOutboundMethod(method),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "capability", String(method));
	}
	assert.deepEqual(RELAY_OUTBOUND_SURFACE
		.filter((method) => REFUSED_AGENT_METHODS.includes(method)), [],
		"a method is both sendable and refused");
});

test("W2929 review: the closed outbound surface rejects unknown methods",
	() => {
		// A deny-list silently widens when an SDK adds a method. `session.reuse`
		// is the frozen contract's explicit example of a capability that does
		// not exist, and a future vendor method is not one of the eight allowed
		// required/optional methods either.
		for (const method of ["session/reuse", "vendor/future_method"]) {
			assert.throws(() => checkOutboundMethod(method),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "capability", method);
		}
	});

test("W2929 re-review: the outbound surface excludes agent-origin methods",
	() => {
		// Direction is part of the closed surface. The pinned SDK places
		// session/update in CLIENT_METHODS, and this module now gives it a
		// separate agent-origin route. A relay-to-agent guard must not also
		// admit that same name in the reverse direction merely because the
		// endpoint is required to present it.
		// Renamed on the review's authority; the assertion is unchanged.
		assert.deepEqual(RELAY_OUTBOUND_SURFACE
			.filter((method) => AGENT_ORIGIN_METHODS.includes(method)), []);
		for (const method of AGENT_ORIGIN_METHODS) {
			assert.throws(() => checkOutboundMethod(method),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "capability", method);
			assert.equal(routeAgentOriginCall(method), method);
		}
	});

test("W2929 correction: the two directional surfaces PARTITION the required five",
	() => {
		// Not merely disjoint — between them they account for every required
		// name, so a member cannot be dropped from both and go unnoticed.
		// The pinned SDK is the authority for which side each falls on:
		// session/update is in CLIENT_METHODS, the other four in
		// AGENT_METHODS.
		const covered = [...RELAY_OUTBOUND_SURFACE, ...AGENT_ORIGIN_METHODS];
		assert.deepEqual(REQUIRED_AGENT_METHODS
			.filter((method) => !covered.includes(method)), [],
			"a required method belongs to neither direction");
		assert.deepEqual(AGENT_ORIGIN_METHODS
			.filter((method) => !REQUIRED_AGENT_METHODS.includes(method)), [],
			"an agent-origin name is not part of the required baseline");
		// And the optional three are relay-origin, so the outbound surface is
		// exactly four plus three.
		assert.equal(RELAY_OUTBOUND_SURFACE.length,
			REQUIRED_AGENT_METHODS.length - AGENT_ORIGIN_METHODS.length
				+ OPTIONAL_AGENT_METHODS.length);
	});

test("W2929: the relay never SERVES a client method, all eight", () => {
	for (const method of CAPABILITY_CLIENT_METHODS) {
		assert.throws(() => serveClientMethod(method),
			// `policy.denied` and not `refused.capability`: the agent is not
			// asking whether the surface exists, it is reaching for one the
			// relay structurally withheld, which is a §4 violation.
			(error) => error instanceof ContractError
				&& error.category === "policy"
				&& error.code === "denied", method);
	}
	// MIGRATED on the review's authority: `session/update` is an AGENT-ORIGIN
	// call and not a client capability, so the routing assertion moved to the
	// boundary that now owns it rather than being dropped. It is asserted
	// there, and here the point is that the client surface serves nothing at
	// all — including a name that IS accepted elsewhere.
	assert.throws(() => serveClientMethod("session/update"),
		(error) => error instanceof ContractError
			&& error.category === "policy"
			&& error.code === "denied");
});

test("W2929 correction: the agent-origin surface accepts one name and denies "
	+ "every other", () => {
		assert.deepEqual([...AGENT_ORIGIN_METHODS], ["session/update"]);
		// The migrated routing assertion, at the boundary that owns it.
		assert.equal(routeAgentOriginCall("session/update"), "session/update");
		// `session/update` is the one member of the required five that flows
		// from the agent to the client, which is why it is the whole list.
		assert.equal(REQUIRED_AGENT_METHODS.includes("session/update"), true);
		for (const method of [...CAPABILITY_CLIENT_METHODS,
		                      ...REFUSED_AGENT_METHODS, "session/prompt",
		                      "vendor/future_notification", "", null,
		                      undefined]) {
			assert.throws(() => routeAgentOriginCall(method),
				(error) => error instanceof ContractError
					&& error.category === "policy"
					&& error.code === "denied", String(method));
		}
	});

test("W2929 review: the withheld client surface denies a future call", () => {
	// §2.2 withholds EVERY client capability. Default-allowing a method not in
	// today's eight-member list makes the next SDK release widen the relay on
	// the day it appears.
	assert.throws(() => serveClientMethod("fs/delete_everything"),
		(error) => error instanceof ContractError
			&& error.category === "policy"
			&& error.code === "denied");
});

test("W2929: advertising a method does not un-refuse it", () => {
	const store = open();
	try {
		// §2.3 refuses these "whether or not advertised". An agent that
		// offers `session/resume` has changed nothing about whether this
		// relay may call it, and the handshake still succeeds — the
		// advertisement is simply not consulted.
		const negotiated = negotiateAcp(store, ACP_PROFILE.document_digest,
			{ ...OFFERED,
			  agentMethods: [...OFFERED.agentMethods, "session/resume",
			                 "session/fork", "session/load"] });
		assert.equal(negotiated.wireVersion, 1);
		for (const method of ["session/resume", "session/fork",
		                      "session/load"]) {
			assert.throws(() => checkOutboundMethod(method),
				(error) => error instanceof ContractError
					&& error.code === "capability", method);
		}
	} finally {
		store.close();
	}
});
