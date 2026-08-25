// W2929 plan item 4, fifth slice: THE HANDSHAKE AND THE CLOSED SURFACE.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance, frozen §2.3:
//
//   "These sets belong to the VERSION, not to a profile. A certified profile
//    does not restate them, and the schema gives it nowhere to. A document
//    that could restate a rule could disagree with it, and a certified
//    profile that disagrees with the policy actually enforced is worse than
//    no profile: it is a second source of truth wearing the first one's
//    authority."
//
// So the four sets below are module constants and the profile never supplies
// them. What a profile DOES supply is which wire it speaks, which version it
// pins, and — for a provider with no version to negotiate — the exact build
// it was certified against.
//
// THE RELAY ADVERTISES ALMOST NOTHING. §2.2 withholds every client capability
// rather than everything unsafe, because "unsafe" is a judgment that has to
// be right every time and "nothing" is a judgment that has to be right once.
// A served client method reaches around the runtime's isolation boundary, so
// the relay refuses the call rather than answering it.
//
// AND EXPERIMENTAL IS DIAGNOSTIC. §2.5 says every surface the underlying
// protocol marks unstable is adapter-private diagnostic material. It may sit
// in the journal and in namespaced diagnostics; it may never reach a
// normalized event, a portable observation, a manifest field, a disposition,
// a gate or an error category.
//
// WRITTEN AGAINST THE FROZEN MODEL, not against the prose alone. The first
// event review caught me building a normalizer against §6.2's table while the
// captured trace said something else, so the constants here are transcribed
// from `evidence/acp_boundary_model.py` and the case file drives them against
// that file's own literals.

import { ContractError, nameValue }
	from "./contracts.mjs";
import { describe, recordFault } from "./records.mjs";
import { certifiedAgentSessionProfile } from "./agent_profile.mjs";

/** The five an agent endpoint MUST present. §2.3, and the version owns it. */
export const REQUIRED_AGENT_METHODS = Object.freeze(["initialize",
	"session/new", "session/prompt", "session/cancel", "session/update"]);

/** Refused in 1.0 whether or not advertised. §2.3.
 *
 *  The history-bearing three — `load`, `resume`, `fork` — are refused for a
 *  specific reason rather than as caution: each imports prior conversation
 *  the manager did not materialize, did not digest-bind into the input
 *  manifest, and cannot attribute to any assignment. W1439 §8.1 binds every
 *  input by digest, and a resumed session is unbound input entering through
 *  the side door. */
export const REFUSED_AGENT_METHODS = Object.freeze(["session/load",
	"session/resume", "session/fork", "session/list", "session/delete",
	"authenticate", "logout", "providers/list", "providers/set",
	"providers/disable", "nes/start", "nes/suggest", "nes/accept",
	"nes/reject", "nes/close", "document/didOpen", "document/didChange",
	"document/didClose", "document/didSave", "document/didFocus",
	"mcp/message"]);

/** ACP CLIENT methods. Serving any one hands the agent a capability that
 *  reaches around the runtime's isolation boundary, so the relay advertises
 *  none of them and REFUSES the call rather than answering it. */
export const CAPABILITY_CLIENT_METHODS = Object.freeze(["fs/read_text_file",
	"fs/write_text_file", "terminal/create", "terminal/output",
	"terminal/release", "terminal/wait_for_exit", "terminal/kill",
	"mcp/connect"]);

/** The six Baton agent-session capabilities. All six are mandatory in 1.0.
 *
 *  `session.reuse` deliberately does not exist: §2.4 says there is nothing to
 *  negotiate, and a capability nobody may decline is not a negotiation. */
export const SESSION_CAPABILITIES = Object.freeze(["session.fresh",
	"session.mode-pin", "session.prompt", "session.cancel",
	"session.update-normalization", "session.permission-refusal"]);

/** Optional, and usable only when the agent advertises it AND the runtime
 *  profile pins its use. §2.3.
 *
 *  All three are relay-origin — the pinned SDK places `session/set_mode`,
 *  `session/set_config_option` and `session/close` in `AGENT_METHODS` — so
 *  all three join the outbound surface below. Whether a particular one may be
 *  used on a particular session is a question about advertisement and the
 *  pinned policy, and it is answered at the composition boundary that has
 *  both, not here, where neither is in hand. */
export const OPTIONAL_AGENT_METHODS = Object.freeze(["session/set_mode",
	"session/set_config_option", "session/close"]);

/** The agent-ORIGIN calls this relay accepts. Exactly one in 1.0.
 *
 *  `session/update` is the one member of the required five that flows from
 *  the agent to the client — the pinned SDK 1.3.0 places it in
 *  `CLIENT_METHODS` while `initialize`, `session/new`, `session/prompt` and
 *  `session/cancel` are in `AGENT_METHODS`. So it is the only inbound name
 *  that is not a client capability. Everything else an agent might call is
 *  either a capability the relay never advertised (§2.2) or a method that
 *  does not exist. */
export const AGENT_ORIGIN_METHODS = Object.freeze(["session/update"]);

/** What the relay may SEND to the agent. Seven names, and DIRECTION is what
 *  makes it seven rather than eight.
 *
 *  Re-review [P1]: this was `required + optional` and therefore still carried
 *  `session/update`, so the two closed directional surfaces I had just
 *  separated overlapped on the one name the separation was about. §2.3's
 *  five-member baseline says what an endpoint must PRESENT across both
 *  directions; it is not a relay-outbound list, and reading it as one put an
 *  agent-to-client notification into a client-to-agent allow list.
 *
 *  DERIVED rather than transcribed, so the two lists cannot drift apart: the
 *  outbound surface is exactly the required baseline minus what the agent
 *  originates, plus the optional three the relay may call when they are
 *  advertised and pinned. A case proves the two are disjoint. */
export const RELAY_OUTBOUND_SURFACE = Object.freeze([
	...REQUIRED_AGENT_METHODS.filter(
		(method) => !AGENT_ORIGIN_METHODS.includes(method)),
	...OPTIONAL_AGENT_METHODS]);

/** What each wire must present. The Codex App Server speaks four methods of
 *  its own, so "required" is a property of the WIRE and not of ACP. */
export const REQUIRED_METHODS_BY_WIRE = Object.freeze({
	acp: REQUIRED_AGENT_METHODS,
	"codex-app-server": Object.freeze(["initialize", "thread/start",
		"turn/start", "turn/interrupt"]),
});

/** The relay's ACP `clientCapabilities` ON THE WIRE, §2.2 verbatim:
 *
 *      { "fs": {}, "terminal": false }
 *
 *  Review [P1]: I had one constant for two different documents. §2.2 and the
 *  pinned SDK 1.3.0 declaration express withholding on the WIRE by ABSENCE —
 *  `readTextFile` and `writeTextFile` are optional members and `fs` is empty
 *  — while the frozen agent-session schema separately records a normalized
 *  snake-case SUMMARY with both members explicitly false. Emitting the
 *  durable summary onto the transport sent field names ACP does not have.
 *
 *  W641 RULED IT — and the ruling went further than the previous round did.
 *  That round named TWO representations and kept both: this wire document and
 *  a normalized snake-case summary the durable schema required. W641 ruled
 *  that the summary is the contract DEFECT rather than a second shape to
 *  name. Agent-session 1.0 keeps ONE representation and it is ACP's: the
 *  profile persists the same structural document the relay sends.
 *
 *  ACP's names and OMISSION semantics are authoritative. An absent
 *  `readTextFile` or `writeTextFile` means that capability was not
 *  advertised, and Baton does not synthesize an explicit false to restate it.
 *
 *  If a future cross-provider consumer needs a provider-neutral capability
 *  model, the ruling says that is separately justified Work with its own
 *  versioned contract — not a translation invented at this boundary. */
export const ACP_CLIENT_CAPABILITIES = Object.freeze({
	fs: Object.freeze({}),
	terminal: false,
});

/** The client-capability members ACP 1.3.0's own declaration marks UNSTABLE.
 *
 *  `session` is stable and is nonetheless not advertised, because §2.2
 *  withholds EVERYTHING rather than everything unsafe. Kept as a named set so
 *  a reader can see that the omission is deliberate rather than an oversight
 *  somebody has to re-derive. */
export const ACP_CLIENT_CAPABILITY_MEMBERS = Object.freeze(["fs", "terminal",
	"session", "plan", "auth", "elicitation", "nes", "positionEncodings"]);
export const ACP_UNSTABLE_CLIENT_CAPABILITIES = Object.freeze(["plan", "auth",
	"elicitation", "nes", "positionEncodings"]);

function certified(store, profileDigest) {
	const profile = certifiedAgentSessionProfile(store, profileDigest);
	if (profile === null) {
		throw new ContractError("policy", "profile-uncertified",
			`${profileDigest} names no currently certified agent-session `
			+ `profile; a handshake is conducted under one or not at all`);
	}
	return profile;
}

/** §2.2 — the relay may advertise no filesystem, terminal or other client
 *  capability, and the comparison is EXACT.
 *
 *  Exact rather than "no dangerous member set", because a subset check
 *  answers the wrong question: it asks whether what is here is safe, when the
 *  rule is that nothing may be here. A member ACP adds next version would
 *  pass a subset check on the day it appeared.
 *
 *  STRUCTURAL, not serialized. Review [P1]: comparing `JSON.stringify` output
 *  made member ORDER part of the rule, and JSON object member order carries
 *  no meaning — the same document written in a different insertion order is
 *  the same document, while a different member or value is a different one.
 *  That is the comparison this is for. */

export function validateClientCapabilities(advertised) {
	const denied = (why) => {
		throw new ContractError("policy", "denied",
			`the relay may advertise no filesystem, terminal or other client `
			+ `capability; ${why}`);
	};
	// THE WHOLE ENVELOPE FIRST, and only then its members. Proving the record
	// before reading `terminal` or `fs` is what makes those reads inert: a
	// data member on a plain record runs nothing, and until the record is
	// proved neither of those things is known.
	const envelope = recordFault(advertised, ["fs", "terminal"]);
	if (envelope !== null) denied(`the offered document ${envelope}`);
	if (advertised.terminal !== false) {
		denied(`terminal is ${describe(advertised.terminal)} and §2.2 sends `
			+ `false`);
	}
	const fs = recordFault(advertised.fs, []);
	if (fs !== null) {
		// ABSENCE is how the wire withholds. A filesystem member present at
		// all — even set false — is a member ACP's optional type did not have
		// to carry, and this boundary is the one place that difference is
		// still visible.
		denied(`fs ${fs}; §2.2 sends {} and the wire withholds by absence`);
	}
}

/** §2.1-§2.4 for ACP: an EXACT wire-version match, or a refusal.
 *
 *  No downgrade. A version the agent answers with is not a negotiation, it is
 *  an announcement, and the profile is what pinned the one this manager
 *  certified against. */
export function negotiateAcp(store, profileDigest,
                             { agentProtocolVersion, agentMethods = [],
                               agentSessionCapabilities = [] } = {}) {
	const profile = certified(store, profileDigest);
	if (profile.wire_protocol !== "acp") {
		throw new ContractError("refused", "unsupported-version",
			`wire-version negotiation belongs to ACP; ${profile.wire_protocol} `
			+ `is certified through its provider binding instead`);
	}
	if (agentProtocolVersion !== profile.pinned_wire_version) {
		throw new ContractError("refused", "unsupported-version",
			`the agent answered wire version `
			+ `${nameValue(agentProtocolVersion)} and the profile `
			+ `pins ${profile.pinned_wire_version}; there is no downgrade`);
	}
	const present = new Set(Array.isArray(agentMethods) ? agentMethods : []);
	const missing = REQUIRED_METHODS_BY_WIRE.acp
		.filter((method) => !present.has(method));
	if (missing.length > 0) {
		throw new ContractError("refused", "capability",
			`this agent endpoint is missing ${missing.join(", ")}; an endpoint `
			+ `that cannot present all five is not an agent endpoint under `
			+ `this contract`);
	}
	const capabilities = new Set(Array.isArray(agentSessionCapabilities)
		? agentSessionCapabilities : []);
	const absent = SESSION_CAPABILITIES
		.filter((capability) => !capabilities.has(capability));
	if (absent.length > 0) {
		throw new ContractError("refused", "capability",
			`this agent session cannot provide ${absent.join(", ")}; all six `
			+ `are mandatory in 1.0`);
	}
	return {
		// THE WIRE DOCUMENT, because this is what the relay sends.
		wireVersion: agentProtocolVersion,
		clientCapabilities: structuredClone(ACP_CLIENT_CAPABILITIES),
		sessionCapabilities: [...SESSION_CAPABILITIES].sort(),
	};
}

/** §2.1 and §10.1 — certification for a provider with NO wire version.
 *
 *  The App Server documents no `protocolVersion` in its initialization, so
 *  there is nothing to negotiate and nothing to refuse a downgrade against.
 *  Certification binds an exact server BUILD and its captured interface
 *  description instead. This REPLACES version negotiation; it is not a second
 *  spelling of it, and the two refuse each other's profiles so neither can be
 *  reached by the wrong door. */
export function bindProvider(store, profileDigest,
                             { observedBuildId,
                               observedInterfaceDigest } = {}) {
	const profile = certified(store, profileDigest);
	if (profile.wire_protocol === "acp") {
		throw new ContractError("refused", "unsupported-version",
			`an ACP profile negotiates a wire version; it is not certified by `
			+ `provider binding`);
	}
	const binding = profile.provider_binding;
	if (binding === null || binding === undefined) {
		throw new ContractError("policy", "profile-uncertified",
			`a provider profile carries a certified provider binding, and `
			+ `${profileDigest} carries none`);
	}
	// A CERTIFIED PROFILE NEVER ENABLES THE EXPERIMENTAL API. §2.5 makes
	// every unstable surface adapter-private diagnostic material, and a
	// binding that switched it on would be certifying exactly the surface
	// that may not reach a portable state.
	//
	// MEASURED AS UNREACHABLE for a certified profile, and said rather than
	// implied: the frozen schema makes `experimental_api` a CONSTANT false,
	// so such a document cannot be certified at all and this line never
	// fires — the case drives the refusal at certification, which is where it
	// actually lands. It is kept because this function reads the binding and
	// a reader should see the rule where the binding is used, not have to
	// find it in a schema three files away. It is not counted as a guard.
	if (binding.experimental_api !== false) {
		throw new ContractError("policy", "denied",
			`a certified profile never enables the provider's experimental `
			+ `API`);
	}
	if (observedBuildId !== binding.server_build_id) {
		throw new ContractError("policy", "profile-uncertified",
			`server build ${nameValue(observedBuildId)} is not `
			+ `the certified ${JSON.stringify(binding.server_build_id)}`);
	}
	if (observedInterfaceDigest !== binding.interface_digest) {
		throw new ContractError("policy", "profile-uncertified",
			`the server's interface description does not match the certified `
			+ `digest ${binding.interface_digest}`);
	}
	return { wireVersion: null, providerBinding: structuredClone(binding) };
}

/** §2.3 — the relay may SEND only a method that exists in 1.0.
 *
 *  Review [P1]: this was a DENY LIST. It rejected the twenty-one names the
 *  contract happens to enumerate and returned every other string, so
 *  `session/reuse` — the frozen contract's own example of a capability that
 *  does not exist — and any future vendor method passed. That is the inverse
 *  of a closed surface, and it recreates exactly the silent widening §2.2
 *  exists to prevent: the next SDK release adds a method and this boundary
 *  admits it on the day it appears.
 *
 *  An allow list has the opposite failure mode, and it is the right one: a
 *  method the contract later adds is refused until somebody adds it here,
 *  which is a conversation rather than a capability.
 *
 *  DIRECTION IS PART OF THE SURFACE. Re-review [P1]: the allow list was the
 *  required five plus the optional three, so it still admitted
 *  `session/update` — a notification the AGENT sends — in the reverse
 *  direction. §2.3's baseline says what an endpoint must present across both
 *  directions and is not a relay-outbound list.
 *
 *  Whether an OPTIONAL method may be used on a particular session depends on
 *  its advertisement and the pinned policy, and neither is in hand at this
 *  boundary. That check belongs to composition; this one answers only whether
 *  the name exists at all. Enforced on the way out rather than trusted to the
 *  advertisement, because §2.3 refuses its list "whether or not advertised". */
export function checkOutboundMethod(method) {
	if (!RELAY_OUTBOUND_SURFACE.includes(method)) {
		throw new ContractError("refused", "capability",
			`${nameValue(method)} is not one of the seven methods `
			+ `this relay may send in agent-session 1.0 `
			+ `(${RELAY_OUTBOUND_SURFACE.join(", ")}); the surface is closed `
			+ `and a name it does not carry is refused whether or not the `
			+ `agent advertises it`);
	}
	return method;
}

/** §4.4 — the relay serves NO client method. Not one, in 1.0.
 *
 *  Review [P1]: this was a deny list over the eight names ACP 1.3.0 happens
 *  to define, so a client method a later SDK adds would have been served by
 *  default. There is nothing to enumerate here: §2.2 advertises no client
 *  capability at all, so every client-directed call is a call on something
 *  the relay structurally withheld, whatever it is named.
 *
 *  `policy.denied` and not `refused.capability`, because the agent is not
 *  asking whether the surface exists — it is reaching around the runtime's
 *  isolation boundary, which is a §4 violation and ends the turn where it
 *  happens. */
export function serveClientMethod(method) {
	throw new ContractError("policy", "denied",
		`the agent called ${nameValue(method)}; this relay `
		+ `advertises no client capability in 1.0, so there is no client `
		+ `method for it to have called`);
}

/** Route one AGENT-ORIGIN call, or deny it. §2.2 and §4.4.
 *
 *  The closed inbound surface, which is one name: `session/update` is the
 *  only member of the required five that flows from the agent to the client.
 *  Everything else is either a capability the relay never advertised or a
 *  method that does not exist, and both are `policy.denied` here — the agent
 *  reaching for something it was not given is a §4 violation regardless of
 *  which of those two it is.
 *
 *  Separated from `serveClientMethod` on the review's authority, because one
 *  function was answering two questions: which client capabilities are served
 *  (none) and which agent-origin calls are accepted (one). */
export function routeAgentOriginCall(method) {
	if (!AGENT_ORIGIN_METHODS.includes(method)) {
		throw new ContractError("policy", "denied",
			`the agent called ${nameValue(method)}; the accepted `
			+ `agent-origin surface is ${AGENT_ORIGIN_METHODS.join(", ")} and `
			+ `nothing else is advertised`);
	}
	return method;
}
