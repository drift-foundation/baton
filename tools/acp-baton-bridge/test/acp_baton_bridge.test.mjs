// W163 slice A acceptance: the generic ACP readiness client against a
// REAL fake-agent subprocess speaking the pinned SDK over stdio.

import test from "node:test";
import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync,
         writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { MAX_TURN_TIMEOUT_MS, validateConfig } from "../src/config.mjs";
import { runBridge as productionRunBridge } from "../src/acp_baton_bridge.mjs";
import { AcpAgentSession, DomainTeardownError }
	from "../src/acp_agent_session.mjs";
import { episodeStillLive, episodeVerdict, validateEnvelope } from "../src/baton_readiness.mjs";
import { AcpSettlement, RECONCILE_MS } from "../src/acp_settlement.mjs";
import { quarantineKey } from "../../codex-event-bridge/src/quarantine_store.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FAKE_AGENT = join(HERE, "fake_acp_agent.mjs");
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

// W49: a Work action carries its assignment EPISODE and the accepted
// configuration generation, and the key must agree with both.
// W11910: `claimed` is the field the readiness LEVEL now turns on, so
// the fixture carries it explicitly.
function workAction(id, { title = "t", episode = 1, generation = 1,
                          claimed = false } = {}) {
	return { kind: "work",
	         action_key: `work:${id}:${episode}:g${generation}`,
	         work: id, episode_seq: episode, config_generation: generation,
	         local_id: id.split("-").pop(), title, phase: "queued",
	         claimed };
}

// W5 slice B: `poke` is a consumed kind now, so it gets a fixture like
// every other one. No `work` field — that absence is the point.
function pokeAction(seq, { asker = "baton.slaw",
                           request = "what's up?" } = {}) {
	return { kind: "poke", action_key: `poke:${seq}`, poke: seq, asker,
	         request, expires_at: null,
	         asked_at: "2026-08-19T03:00:00Z" };
}

function envelope(actions, { timedOut = false,
                             participant = "baton.claude",
                             uuid = UUID } = {}) {
	return {
		protocol_version: 11,
		projection_version: "7.0",
		participant,
		authority_uuid: uuid,
		snapshot_seq: 42,
		result: { actionable: actions, timed_out: timedOut },
	};
}

test("ACP readiness accepts the projection-8 participant-action contract", () => {
	const payload = envelope([]);
	payload.projection_version = "8.0";
	assert.equal(validateEnvelope(payload, "baton.claude").projection_version,
	             "8.0");
});

test("ACP readiness accepts the projection-9 candidate contract", () => {
	// W38 moved the major because the PHASE value set changed. The
	// envelope's own fields did not, so this consumer must accept 9 in
	// the same candidate that ships it — a readiness bridge one major
	// behind is a silent outage, which is how projection 8 was found.
	const payload = envelope([]);
	payload.projection_version = "9.0";
	assert.equal(validateEnvelope(payload, "baton.claude").projection_version,
	             "9.0");
});

test("ACP readiness accepts projection 11 and still refuses an unsupported future major", () => {
	// W155: the tree window moved to three levels, which added a value
	// to the consumed `depth` domain — a breaking change under the
	// projection file's own same-major rule — so the major moved to 11
	// and this consumer moves with it in the SAME candidate. The
	// participant-action envelope's own fields did not change.
	const payload = envelope([]);
	// W5: projection 12 carries the `poke` action kind. A consumer built
	// before the tolerance widening REFUSES an envelope containing it,
	// which is the documented major-version condition — so the major
	// moved and this consumer moves with it in the SAME candidate.
	for (const supported of ["10.0", "11.0", "12.0"]) {
		payload.projection_version = supported;
		assert.equal(validateEnvelope(payload, "baton.claude").projection_version,
		             supported);
	}
	payload.projection_version = "13.0";
	assert.throws(() => validateEnvelope(payload, "baton.claude"),
	              /projection-7\/8\/9\/10\/11\/12 participant-action contract/);
});

// W101: `role` is a required launch input, so the rig supplies one by
// default. A test that cares about its absence builds the config
// directly and asserts the refusal.
// W28681: `turnTimeoutMs` is MANDATORY configuration with no default, so
// the rig names one. Generous by default — a case about session
// selection or the launcher contract must not fail because a fake agent
// was slow — and overridden to a few milliseconds by the cases that are
// about the deadline itself.
// W55705 (approver ruling M58455): `runtime.actionOwner` is MANDATORY for a
// managed ACP bridge, because the post-turn claim settlement owes one durable
// incident and an ownerless incident is refused. The rig names one so every
// case that is about something else still describes a startable deployment.
const ACTION_OWNER = "baton.slaw";

function rig({ env = {}, participant = "baton.claude",
               role = "impl", sessionMode = "new", policyResources,
               runtime = { actionOwner: ACTION_OWNER },
               turnTimeoutMs = 120000 } = {}) {
	const home = mkdtempSync(join(tmpdir(), "acp-bridge-"));
	const log = join(home, "agent-log.jsonl");
	writeFileSync(log, "");
	const policy = policyResources ?? [join(home, "policy.json")];
	if (!policyResources) writeFileSync(policy[0], "{}\n");
	const config = validateConfig({
		baton: { binary: "/unused/baton", config: "/unused/baton.json",
		         participant, role },
		agent: { command: process.execPath,
		         args: [FAKE_AGENT],
		         env: { FAKE_ACP_LOG: log, ...env },
		         cwd: home },
		session: { mode: sessionMode, cwd: home },
		permissionMode: "bypassPermissions",
		policyResources: policy,
		stateDir: join(home, "state"),
		retryMs: 25,
		turnTimeoutMs,
		...(runtime ? { runtime } : {}),
	});
	return { home, log, config };
}

// W27 R2: a `load` run resolves its selection at STARTUP, so any test
// that means to exercise something LATER in the load path must give the
// run a valid selection to resolve. This seeds the fixture only; it
// changes no assertion.
function seedSelection(config, sessionId) {
	mkdirSync(config.stateDir, { recursive: true });
	writeFileSync(join(config.stateDir, "session.json"),
	              `${JSON.stringify({ sessionId }, null, 2)}\n`);
	return sessionId;
}

function events(log) {
	return readFileSync(log, "utf8").trim().split("\n")
		.filter(Boolean).map((line) => JSON.parse(line));
}

function script(steps) {
	let calls = 0;
	const controller = new AbortController();
	return {
		signal: controller.signal,
		runWait: async () => {
			if (calls >= steps.length) {
				controller.abort();
				const error = new Error("aborted");
				error.name = "AbortError";
				throw error;
			}
			const step = steps[calls++];
			// W11910: a step may be a thunk, so a test can advance its
			// own clock between two polls and assert a retry DEADLINE
			// rather than sleep through one.
			return typeof step === "function" ? step() : step;
		},
	};
}

const quiet = { info() {}, warn() {} };

// W11910: an offer retry has a DEADLINE, so every run gets a clock it
// controls. Frozen unless a test advances it deliberately — otherwise
// whether a bounded retry fired would depend on how long the fake agent
// happened to take.
function clock(start = 1_000_000) {
	let value = start;
	return { now: () => value, advance(ms) { value += ms; return value; } };
}

const runBridge = (config, options = {}) => productionRunBridge(config, {
	loadInstructions: async () => ({
		participant: config.baton.participant,
		role: config.baton.role ?? "impl",
		instructions: "Honor the configured participant role.",
		configurationGeneration: 1,
	}),
	now: clock().now,
	...options,
});

test("initialize and mode negotiation complete before any prompt", async () => {
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const seen = events(log).map((entry) => entry.event);
	const order = ["initialize", "session/new", "session/set_mode",
	               "prompt/start"];
	const positions = order.map((event) => seen.indexOf(event));
	assert.ok(positions.every((at) => at >= 0),
		`missing lifecycle events: ${seen.join(",")}`);
	assert.deepEqual([...positions].sort((a, b) => a - b), positions,
		"initialize/session/mode did not precede the prompt");
	const mode = events(log).find((entry) => entry.event === "session/set_mode");
	assert.equal(mode.modeId, "bypassPermissions");
});

test("a readiness action prompts the configured session with the compact line", async () => {
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163", { title: "acp client" })]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompt = events(log).find((entry) => entry.event === "prompt/start");
	assert.ok(prompt, "no prompt reached the agent");
	assert.match(prompt.text, /^\[BATON READY\] v11 Work W163 \(acp client\)/);
	// W14828: the compact line is UNCHANGED and is no longer the whole
	// prompt. It ends at the policy cue exactly as before — the anchor moved
	// from the end of the text to the end of the LINE — and the authoritative
	// launcher block follows it, because the role prose says a deployment
	// supplies an exact binary and config while naming neither.
	assert.match(prompt.text, /^.*Apply standing v11 Baton policy\.$/m);
	assert.equal(prompt.mode, "bypassPermissions",
		"the turn ran outside the configured mode");
	assert.doesNotMatch(prompt.text, /body|EXTERNAL EVENT/);
});

// -- W14828: the launcher contract reaches the turn ------------------------
//
// `work/records/2026/08/finding-acp-launcher-contract-drift/`.
//
// The incident, in one sentence: a healthy restart rendered the correct
// executable, config, participant and role into the runtime context, the
// prompt and the spawned environment carried none of them, and the fresh
// model went looking — found a persistent participant file still pinned to a
// retired deployment, and made its first `claim` through an executable that
// refused the live authority. The claim failed while the authority still
// showed Work claimed by that participant.
//
// The suite was 69/69 green through all of it, because nothing asserted that
// either carrier held a launcher value. That is the measured gap these close.

const LAUNCHER = [
	'BATON_BIN="/unused/baton"',
	'BATON_CONFIG="/unused/baton.json"',
	'BATON_PARTICIPANT="baton.claude"',
	'BATON_ROLE="impl"',
];

function launcherEnv(log) {
	return events(log).find((entry) => entry.event === "launcher/env");
}

test("every action kind carries the launcher contract exactly once",
async () => {
	// EVERY KIND, because each one can require a canonical Baton operation —
	// a Work claim, an obligation answer, a trial, a poke answer — and a
	// context that had the values for one and not the others would go looking
	// on exactly the turns that did not carry them.
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([
			workAction("7ba67cb8-W163"),
			{ kind: "obligation", action_key: "obligation:9",
			  work: "7ba67cb8-W2", seq: 9, flavor: "response" },
			{ kind: "due_trial", action_key: "trial:7ba67cb8-W3:1:1",
			  work: "7ba67cb8-W3", trial: 1, deadline_generation: 1,
			  review_at: "2026-08-16T12:00:00Z" },
			pokeAction(4)]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 4, "not every kind reached the agent");
	for (const prompt of prompts) {
		for (const line of LAUNCHER) {
			assert.equal(prompt.text.split(line).length - 1, 1,
				`${line} is not present exactly once in ${prompt.text}`);
		}
		assert.match(prompt.text,
			/Baton launcher contract \(authoritative; do not infer\):/);
		assert.match(prompt.text,
			/Invoke BATON_BIN with --config BATON_CONFIG and --participant BATON_PARTICIPANT for every Baton operation\./);
	}
});

test("a loaded session gets the same contract as a new one", async () => {
	// Both session modes, because the incident happened on a RESTART: the
	// turn that goes looking for a launcher is the first turn of a fresh
	// model, whichever way its session was selected.
	const { log, config } = rig({ sessionMode: "load" });
	seedSelection(config, "session-load-1");
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompt = events(log).find((entry) => entry.event === "prompt/start");
	for (const line of LAUNCHER) assert.ok(prompt.text.includes(line), line);
});

test("the spawned agent observes the four values even when the template omits them",
async () => {
	// THE OTHER CARRIER, and the one the shipped templates did not spell.
	// `rig()` supplies no BATON_* entries at all — exactly the live
	// `baton.claude` template's shape — so what the child sees here is
	// derived from the accepted `baton` section or it is nothing.
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	assert.deepEqual(launcherEnv(log), {
		at: launcherEnv(log).at, event: "launcher/env",
		BATON_BIN: "/unused/baton", BATON_CONFIG: "/unused/baton.json",
		BATON_PARTICIPANT: "baton.claude", BATON_ROLE: "impl",
	}, "the spawned agent did not inherit the derived launcher contract");
});

test("a stale inherited launcher value does not survive into the child",
async () => {
	// The ambient carrier, which is what the persistent file effectively was:
	// a plausible value from somewhere nobody validated. The parent exports a
	// RETIRED deployment's binary here — the exact shape of the incident —
	// and the derived value has to win, because `{...process.env, ...env}`
	// only helps if the derived entries are in `env`.
	const previous = process.env.BATON_BIN;
	process.env.BATON_BIN = "/home/sl/opt/baton/v11/fc613e3/bin/baton";
	try {
		const { log, config } = rig();
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet });
		assert.equal(launcherEnv(log).BATON_BIN, "/unused/baton",
			"a retired deployment inherited from the parent reached the agent");
	} finally {
		if (previous === undefined) delete process.env.BATON_BIN;
		else process.env.BATON_BIN = previous;
	}
});

test("an explicitly conflicting launcher value refuses the configuration",
async () => {
	// FAIL CLOSED, AND BY KEY. An operator template may still spell these —
	// existing ones do — but only to the same values. A second spelling that
	// disagrees is the drift this Work exists to remove, so it refuses before
	// instructions are read, before the wait, before any spawn or prompt,
	// rather than being resolved in favour of one side.
	for (const [key, value] of [
			["BATON_BIN", "/home/sl/opt/baton/v11/fc613e3/bin/baton"],
			["BATON_CONFIG", "/home/sl/baton-v11/baton.json"],
			["BATON_PARTICIPANT", "baton.codex"],
			["BATON_ROLE", "rview"]]) {
		assert.throws(() => rig({ env: { [key]: value } }),
			new RegExp(`agent\\.env\\.${key} is `),
			`${key} was allowed to disagree with the baton section`);
	}
	// And the same values spelled explicitly are FINE, which is what keeps
	// the existing templates working.
	const { log, config } = rig({ env: {
		BATON_BIN: "/unused/baton", BATON_CONFIG: "/unused/baton.json",
		BATON_PARTICIPANT: "baton.claude", BATON_ROLE: "impl" } });
	assert.equal(config.agent.env.BATON_BIN, "/unused/baton");
	assert.ok(log);
});

test("two participants sharing one binary receive their own values",
async () => {
	// Identity isolation. One deployment runs several ACP participants
	// against one authority, and a context handed the other one's identity
	// would claim as somebody else — which is the failure mode that is worse
	// than not claiming at all.
	const mine = rig({ participant: "baton.claude", role: "impl" });
	const theirs = rig({ participant: "baton.tuner", role: "tuner" });
	for (const [{ log, config }, participant, role] of [
			[mine, "baton.claude", "impl"], [theirs, "baton.tuner", "tuner"]]) {
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")], { participant }),
		]);
		await runBridge(config, { signal, runWait, logger: quiet });
		const prompt = events(log).find((entry) => entry.event === "prompt/start");
		assert.ok(prompt.text.includes(`BATON_PARTICIPANT=${JSON.stringify(participant)}`));
		assert.ok(prompt.text.includes(`BATON_ROLE=${JSON.stringify(role)}`));
		assert.equal(launcherEnv(log).BATON_PARTICIPANT, participant);
		assert.equal(launcherEnv(log).BATON_ROLE, role);
	}
	assert.notEqual(launcherEnv(mine.log).BATON_PARTICIPANT,
	                launcherEnv(theirs.log).BATON_PARTICIPANT);
});

test("the block carries the four values and nothing else about the deployment",
async () => {
	// NO INFERENCE, and no over-sharing. The block is a locator, not a
	// context dump: an action owner, a policy resource path, the state
	// directory or a session id in it would be four more things a model
	// could reason from, and the confirmed boundary is that it reasons from
	// these four and asks the authority for the rest.
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompt = events(log).find((entry) => entry.event === "prompt/start");
	const block = prompt.text.split("Baton launcher contract")[1];
	assert.ok(block, "no launcher block in the prompt");
	for (const absent of [config.stateDir, config.policyResources[0],
	                      config.agent.cwd, "load.json", "bootstrap.json"]) {
		assert.ok(!block.includes(absent),
			`the launcher block leaked ${absent}`);
	}
	// SIX LINES AND NO MORE: the header, the four values, the invocation
	// sentence. Counted rather than described, so a fifth value added later
	// has to be a deliberate change to this number.
	const whole = prompt.text.split("\n\n").slice(1).join("\n\n");
	assert.equal(whole.trim().split("\n").length, 6,
		`the launcher block is not the six lines it should be:\n${whole}`);
});

test("an unreadable action kind is ignored and the known work still reaches the agent", async () => {
	// W5 (finding-conversational-agent-poke), ruled 2026-08-18. Before
	// this widening the shared validator threw on an unknown kind, which
	// refused the WHOLE envelope — so the first authority to emit a
	// fourth kind would have stopped this agent receiving its ordinary
	// Work and obligation wakes too. The point of the test is the entry
	// BESIDE the unreadable one: it must still be delivered.
	const { log, config } = rig();
	const warnings = [];
	const { signal, runWait } = script([
		envelope([{ kind: "some_future_kind", action_key: "future:7" },
		          workAction("7ba67cb8-W163", { title: "acp client" })]),
		// still pending on the next poll: the diagnostic is a BUILD-level
		// skew and must not repeat once per poll
		envelope([{ kind: "some_future_kind", action_key: "future:7" }]),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });

	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 1, "the known Work action was not delivered");
	assert.match(prompts[0].text, /^\[BATON READY\] v11 Work W163/);
	// nothing about the unreadable entry reached the agent
	assert.doesNotMatch(prompts[0].text, /future_kind/);

	const skew = warnings.filter((message) => /unknown to this build/.test(message));
	assert.equal(skew.length, 1,
		`expected exactly one skew diagnostic, got ${JSON.stringify(warnings)}`);
	assert.match(skew[0], /"some_future_kind"/);
	assert.match(skew[0], /future:7/);
});

test("a poke wakes the agent with the question and how to answer it", async () => {
	// W5 slice B. Tolerating and dropping the entry was the compatibility
	// prerequisite; this is the feature. The agent must receive the
	// friendly question and enough structured identity to answer through
	// `poke-answer` without re-reading the projection to find the seq.
	const { log, config } = rig();
	const { signal, runWait } = script([
		envelope([pokeAction(7, { asker: "baton.slaw",
		                          request: "still on W12?" })]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompt = events(log).find((entry) => entry.event === "prompt/start");
	assert.ok(prompt, "the poke never reached the agent");
	assert.match(prompt.text, /baton\.slaw asks baton\.claude: still on W12\?/);
	assert.match(prompt.text, /poke-answer poke=7/);
	assert.match(prompt.text, /state=idle\|working\|waiting\|needs-help/);
	assert.match(prompt.text, /reading your canonical Baton state first/);
	// conversational, not an alarm: the contract says the wording must
	// not read as an escalation or a health verdict
	assert.doesNotMatch(prompt.text, /alert|alarm|escalat|fail|unhealthy/i);
});


test("a poke never displaces the Work and obligation wakes beside it", async () => {
	// The ruling: repeat delivery stays idempotent and a poke does not
	// displace ordinary actions. Both halves, on one screenful.
	const { log, config } = rig();
	const work = workAction("7ba67cb8-W163", { title: "acp client" });
	const poke = pokeAction(9);
	const { signal, runWait } = script([
		envelope([work, poke]),
		envelope([work, poke]),          // unchanged: nothing re-delivers
		envelope([], { timedOut: true }),
		envelope([work, poke]),          // returning keys deliver again
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start")
		.map((entry) => entry.text);
	assert.equal(prompts.length, 4, prompts);
	// the Work action is delivered first and is not swallowed by the
	// poke sharing its envelope
	assert.match(prompts[0], /^\[BATON READY\] v11 Work W163/);
	assert.match(prompts[1], /asks baton\.claude/);
	assert.match(prompts[2], /^\[BATON READY\] v11 Work W163/);
	assert.match(prompts[3], /asks baton\.claude/);
});


test("a persistent set is level-triggered and a returning key re-delivers", async () => {
	const { log, config } = rig();
	const set = [workAction("7ba67cb8-W163")];
	const { signal, runWait } = script([
		envelope(set), envelope(set),
		envelope([], { timedOut: true }),
		envelope(set),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 2,
		"suppression or rediscovery broke: expected exactly 2 deliveries");
});

test("busy sessions serialize wakes; turns never overlap", async () => {
	// W11910 replaced this fixture. It used to feed THREE unclaimed Work
	// actions and require three model turns, which is exactly the
	// behaviour the claim-slot rule forbids: a participant holds at most
	// one claim, so offering the second and third before the first is
	// resolved spends turns to reach a refusal. The property under test
	// was never about Work — it is that a busy session is never steered
	// by a second wake — so it is asserted on three actions that DO all
	// belong in one poll. One-at-a-time Work admission has its own tests
	// below.
	const { log, config } = rig({ env: { FAKE_ACP_SLOW_MS: "120" } });
	const { signal, runWait } = script([
		envelope([pokeAction(1), pokeAction(2), pokeAction(3)]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const trail = events(log).filter((entry) =>
		entry.event === "prompt/start" || entry.event === "prompt/end");
	assert.equal(trail.length, 6);
	for (let index = 0; index < trail.length; index += 2) {
		assert.equal(trail[index].event, "prompt/start");
		assert.equal(trail[index + 1].event, "prompt/end");
		assert.equal(trail[index].text, trail[index + 1].text,
			"turns interleaved: a second wake steered a busy session");
	}
});

// -- W11910: readiness stays armed until the canonical claim ------------
//
// `work/records/2026/08/finding-readiness-offer-cleared-before-claim/`.
//
// The incident: W6630, W6632, W6633 and W10265 sat ready, unclaimed and
// overdue while this participant's runner reported idle. Each had been
// delivered once, each turn had returned without claiming — an obsolete
// CLI in three cases, an occupied claim slot in the fourth — and a
// returned prompt was recorded as if it were an acknowledgement. Only
// restarting the bridge, which happens to empty its memory, recovered
// them. These are the cases that say a completed turn is not a claim.

test("a turn that did not claim keeps the offer armed, without a restart", async () => {
	const { log, config } = rig();
	const time = clock();
	const offer = workAction("7ba67cb8-W6630");
	const { signal, runWait } = script([
		envelope([offer]),
		// unchanged canonical state, still inside the retry deadline:
		// the offer is retained, not spent again
		envelope([offer]),
		// past the deadline: the SAME process offers the SAME key again
		() => { time.advance(config.retryMs * 8); return envelope([offer]); },
	]);
	await runBridge(config, { signal, runWait, now: time.now, logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 2,
		"a turn that never claimed cleared the offer, or it busy-looped");
	assert.equal(prompts[0].text, prompts[1].text);
	assert.match(prompts[0].text, /W6630.*ready and unclaimed/);
	assert.equal(
		events(log).filter((entry) => entry.event === "session/new").length, 1,
		"recovery required a new session: this must not need a restart");
});

test("a claim acknowledges the offer and no second turn is spent on it", async () => {
	const { log, config } = rig();
	const time = clock();
	const offer = workAction("7ba67cb8-W163");
	// claiming does NOT change the action key: only `claimed` flips.
	const taken = workAction("7ba67cb8-W163", { claimed: true });
	const { signal, runWait } = script([
		envelope([offer]),
		// far past any retry deadline — it is the CLAIM that clears the
		// offer here, not the clock
		() => { time.advance(600_000); return envelope([taken]); },
		() => { time.advance(600_000); return envelope([taken]); },
	]);
	await runBridge(config, { signal, runWait, now: time.now, logger: quiet });
	assert.equal(
		events(log).filter((entry) => entry.event === "prompt/start").length, 1,
		"the claim did not acknowledge the offer it answered");
});

test("a bridge starting on a live claim still delivers one recovery prompt",
async () => {
	// The other half of the contract: a participant's own claimed Work is
	// still theirs to finish, and a runner that only looked for unclaimed
	// Work would walk past it. Seen for the first time, it is delivered
	// once; the claim it recovers is its own acknowledgement.
	const { log, config } = rig();
	const claimed = workAction("7ba67cb8-W2907", { claimed: true });
	const { signal, runWait } = script([
		envelope([claimed]), envelope([claimed]), envelope([claimed]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 1, "claimed-Work restart recovery changed");
	assert.match(prompts[0].text, /W2907.*claimed by you/);
});

test("a claimed-Work recovery prompt that FAILED is delivered again",
async () => {
	// Review [P1]. The recovery wake for a Work first seen already
	// claimed was created as a `pending` offer — and on the next
	// unchanged poll the `claimed:true` branch acknowledged it. That
	// reads "the offer was answered by a claim" from a state that
	// actually meant "the prompt never reached the runner", so a
	// participant whose recovery prompt failed once sat on a live claim
	// with no wake and no retry until somebody restarted the process:
	// the exact restart-dependent stall this Work removes.
	const { config } = rig();
	const claimed = workAction("7ba67cb8-W2907", { claimed: true });
	const { signal, runWait } = script([
		envelope([claimed]), envelope([claimed]), envelope([claimed]),
	]);
	const prompts = [];
	let attempt = 0;
	await runBridge(config, {
		signal, runWait, logger: quiet,
		sessionFactory: () => ({
			alive: () => true,
			sessionId: "sess-1",
			async start() { return "sess-1"; },
			async promptText(text) {
				attempt += 1;
				// The first delivery fails the way a real one does: the
				// prompt throws, so `markPresented` is never reached.
				if (attempt === 1) throw new Error("transport closed");
				prompts.push(text);
			},
			async stop() {},
		}),
	});
	assert.equal(attempt > 1, true,
		"the failed recovery prompt was never attempted again");
	assert.equal(prompts.length, 1,
		"the repaired recovery prompt was delivered "
		+ `${prompts.length} times; one claim is recovered once`);
	assert.match(prompts[0], /W2907.*claimed by you/);
});

test("a claimed-Work recovery prompt that SUCCEEDED is never repeated",
async () => {
	// The other half of the same distinction: `recovering` must not turn
	// the one recovery wake into a level that re-prompts every poll.
	const { config } = rig();
	const claimed = workAction("7ba67cb8-W2907", { claimed: true });
	const { signal, runWait } = script([
		envelope([claimed]), envelope([claimed]), envelope([claimed]),
		envelope([claimed]), envelope([claimed]),
	]);
	const prompts = [];
	await runBridge(config, {
		signal, runWait, logger: quiet,
		sessionFactory: () => ({
			alive: () => true,
			sessionId: "sess-1",
			async start() { return "sess-1"; },
			async promptText(text) { prompts.push(text); },
			async stop() {},
		}),
	});
	assert.equal(prompts.length, 1,
		`the claim was re-prompted ${prompts.length} times`);
});

test("an unclaimed offer waits for the claim slot and arrives when it frees",
async () => {
	// The W10265 shape exactly: delivered while W6627 was held, correctly
	// not claimed, and then never offered again. The offer must survive
	// the wait and land without any restart.
	const { log, config } = rig();
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	const waiting = workAction("7ba67cb8-W10265");
	const { signal, runWait } = script([
		envelope([held, waiting]),
		envelope([held, waiting]),
		// W6627 was passed and closed; the slot is free
		envelope([waiting]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start").map((e) => e.text);
	assert.equal(prompts.length, 2, prompts);
	assert.match(prompts[0], /W6627.*claimed by you/);
	assert.match(prompts[1], /W10265.*ready and unclaimed/);
	assert.equal(
		events(log).filter((entry) => entry.event === "session/new").length, 1,
		"the retained offer needed a new session to be rediscovered");
});

test("the ACP launcher contract refuses a relative executable or config",
async () => {
	// W12229: this family's half of the same contract. `baton.binary` and
	// `baton.config` become BATON_BIN and BATON_CONFIG in the agent's own
	// environment, and a relative one is an inferred location wearing the
	// shape of an explicit value.
	//
	// Found while correcting the Codex bootstrap door under review [P1]:
	// the Codex dispatcher had always required this and the Codex
	// bootstrap did not, and neither did this one. Three doors into one
	// contract, and only one of them was closed.
	// A real policy resource, because `validateConfig` reads them: this
	// case is about the two launcher paths and must not be refused for
	// something else first.
	const home = mkdtempSync(join(tmpdir(), "acp-w12229-"));
	const policy = join(home, "policy.json");
	writeFileSync(policy, "{}\n");
	const base = {
		baton: { binary: "/opt/baton/bin/baton",
			config: "/home/op/baton.json",
			participant: "baton.claude", role: "impl" },
		agent: { command: "/opt/acp/agent", cwd: home },
		session: { mode: "load", cwd: home },
		permissionMode: "bypassPermissions",
		policyResources: [policy],
		stateDir: join(home, "state"),
		runtime: { actionOwner: ACTION_OWNER },
		// W28681: named so this case is refused for the launcher path it
		// is about rather than for the deadline it is not.
		turnTimeoutMs: 60000,
	};
	for (const [key, value] of [["binary", "bin/baton"],
	                            ["binary", "./bin/baton"],
	                            ["config", "state/baton.json"],
	                            ["config", "../baton.json"]]) {
		assert.throws(
			() => validateConfig({ ...base,
				baton: { ...base.baton, [key]: value } }),
			new RegExp(`baton\\.${key} must be an absolute path`),
			`a relative baton.${key} of ${value} was accepted`);
	}
	// And the ordinary absolute pair still validates.
	assert.equal(validateConfig(base).baton.binary, "/opt/baton/bin/baton");
});

test("a claim acquired between polling and the ACP turn defers the offer",
async () => {
	// The first envelope saw a free slot, but the authority says another
	// Work owns it at the immediate pre-turn read. That is neither delivery
	// nor withdrawal: the same offer remains armed and arrives after the
	// slot is free.
	const { config } = rig();
	const time = clock();
	const waiting = workAction("7ba67cb8-W10265");
	const { signal, runWait } = script([
		envelope([waiting]),
		() => {
			time.advance(config.retryMs * 8);
			return envelope([waiting]);
		},
	]);
	const trail = [];
	let checks = 0;
	await runBridge(config, {
		signal, runWait, now: time.now, logger: quiet,
		revalidate: async () => {
			const verdict = checks++ === 0 ? "deferred" : "live";
			trail.push(verdict);
			return verdict;
		},
		sessionFactory: () => ({
			alive: () => true,
			sessionId: "sess-1",
			async start() { return "sess-1"; },
			async promptText() { trail.push("prompt"); },
			async stop() {},
		}),
	});
	assert.deepEqual(trail, ["deferred", "live", "prompt"],
		"the ACP adapter spent a turn while another Work held the claim slot");
});

test("two unclaimed Works yield only the canonical head until its outcome is known",
async () => {
	const { log, config } = rig();
	const first = workAction("7ba67cb8-W6630");
	const second = workAction("7ba67cb8-W6632");
	const { signal, runWait } = script([
		envelope([first, second]),
		// the head's claim-slot outcome is now known — canonical state
		// still says unclaimed — so the next offer may take its turn
		envelope([first, second]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start").map((e) => e.text);
	assert.equal(prompts.length, 2, prompts);
	assert.match(prompts[0], /W6630/);
	assert.match(prompts[1], /W6632/);
});

test("non-Work actions beside a deferred Work keep their own delivery rule",
async () => {
	// W11910's property, and it is UNCHANGED: the one-claim Work slot governs
	// Work offers and nothing else, so the poke is not deferred BY THAT RULE
	// and the unclaimed W10265 still is.
	//
	// W55705 return review (2026-09-01T05:03:30Z) [P1] SUPERSEDES THE COUNT.
	// Delivering the claimed recovery wake mints a settlement fence -- the
	// turn ended while that claim survived, which is this Work's whole defect
	// state -- and the ruling retains every LATER wake until the exact claim
	// is reconciled. So the poke is retained here by the settlement fence
	// rather than by the claim-slot rule, which is a different gate for a
	// different reason. Retained, not withdrawn: it is offered again on the
	// next poll once the claim is gone, and the case below proves that.
	//
	// FLAGGED RATHER THAN QUIETLY EDITED. This is an accepted prior case whose
	// expectation the return review's required correction moves; the reviewer
	// accepts or overrules it.
	const { log, config } = rig();
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	const waiting = workAction("7ba67cb8-W10265");
	const { signal, runWait } = script([
		envelope([held, waiting, pokeAction(9)]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start").map((e) => e.text);
	assert.equal(prompts.length, 1, prompts);
	assert.match(prompts[0], /W6627.*claimed by you/);
	assert.ok(!prompts.some((text) => /W10265/.test(text)),
		"an unclaimed offer was delivered into an occupied claim slot");
	assert.ok(!prompts.some((text) => /asks baton\.claude/.test(text)),
		"a later wake was spent while the exact claim was unreconciled");
});

test("a retained later wake is delivered once the exact claim is reconciled",
async () => {
	// The other half of the correction above, and the reason `retained` is
	// the right word: the poke is not withdrawn, it is waiting. A canonical
	// read that says the slot is free clears the fence and the same poke goes
	// through on the next poll, without anybody restarting this process.
	const { log, config } = rig();
	const spy = runtimeSpy();
	const time = clock();
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	const poke = pokeAction(9);
	const { signal, runWait } = script([
		envelope([held, poke]),
		() => { time.advance(RECONCILE_MS + 1); return envelope([poke]); },
	]);
	const settlement = settlementFor(config, {
		spy, now: time.now,
		reads: [slot([held]), slot([]), slot([])] });
	await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
		runtime: spy.runtime, settlement });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start").map((e) => e.text);
	assert.equal(prompts.length, 2, prompts);
	assert.match(prompts[0], /W6627.*claimed by you/);
	assert.match(prompts[1], /asks baton\.claude/);
});

test("a retained offer withdrawn while it waits is never delivered", async () => {
	// Blocked, rerouted, parked, superseded or closed: the key stops
	// being actionable, and the local offer goes with it.
	const { log, config } = rig();
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	const waiting = workAction("7ba67cb8-W10265");
	const { signal, runWait } = script([
		envelope([held, waiting]),
		envelope([held]),
		envelope([], { timedOut: true }),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const prompts = events(log)
		.filter((entry) => entry.event === "prompt/start").map((e) => e.text);
	assert.equal(prompts.length, 1, prompts);
	assert.match(prompts[0], /W6627.*claimed by you/);
});

test("an unexpected permission request under bypass is cancelled and fails the delivery", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_PERMISSION: "1" } });
	const warnings = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	const outcome = events(log).find((entry) =>
		entry.event === "permission/outcome");
	assert.equal(outcome.outcome.outcome, "cancelled",
		"the permission request was not cancelled");
	assert.ok(warnings.some((line) =>
		/policy\/protocol failure/.test(line)),
		"the violation was not reported");
	assert.ok(warnings.some((line) =>
		/could not deliver work:7ba67cb8-W163/.test(line)),
		"the delivery did not fail visibly");
});

test("agent exit mid-turn is visible, retried, and readiness survives", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_EXIT_ON_PROMPT: "1" } });
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope(set);
			if (calls === 2) {
				// the crashing agent config is replaced mid-run: the
				// SAME undelivered key must now reach the healthy agent
				delete config.agent.env.FAKE_ACP_EXIT_ON_PROMPT;
				return envelope(set);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: { info() {}, warn(message) { warnings.push(message); } },
	});
	assert.ok(warnings.some((line) => /could not deliver/.test(line)),
		"the crash was not visible");
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 2,
		"readiness was discarded by the crash instead of retried");
	assert.equal(prompts[1].text, prompts[0].text);
});

test("two participants cannot cross-deliver readiness", async () => {
	const one = rig({ participant: "baton.claude" });
	const two = rig({ participant: "baton.gemini" });
	const claudeAction = workAction("7ba67cb8-W163");
	const geminiAction = workAction("7ba67cb8-W900");
	await runBridge(one.config, {
		...script([envelope([claudeAction], { participant: "baton.claude" })]),
		logger: quiet });
	await runBridge(two.config, {
		...script([envelope([geminiAction], { participant: "baton.gemini" })]),
		logger: quiet });
	const claudePrompts = events(one.log)
		.filter((entry) => entry.event === "prompt/start");
	const geminiPrompts = events(two.log)
		.filter((entry) => entry.event === "prompt/start");
	assert.equal(claudePrompts.length, 1);
	assert.equal(geminiPrompts.length, 1);
	assert.match(claudePrompts[0].text, /W163.*baton\.claude/);
	assert.doesNotMatch(claudePrompts[0].text, /W900|baton\.gemini/);
	assert.match(geminiPrompts[0].text, /W900.*baton\.gemini/);
	assert.doesNotMatch(geminiPrompts[0].text, /W163|baton\.claude/);
});

test("a wrong-participant envelope refuses and nothing reaches the agent", async () => {
	const { log, config } = rig({ participant: "baton.claude" });
	const warnings = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")],
		         { participant: "baton.codex" }),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	assert.ok(warnings.some((line) => /participant/.test(line)));
	assert.ok(!events(log).some((entry) => entry.event === "prompt/start"),
		"a foreign participant's readiness reached this agent");
});

test("session mode=load resumes the persisted session across restart", async () => {
	const { log, config } = rig();
	await runBridge(config, {
		...script([envelope([workAction("7ba67cb8-W163")])]),
		logger: quiet });
	const born = events(log).find((entry) => entry.event === "session/new");
	assert.ok(born.sessionId);
	// second bridge process: same state dir, mode=load
	config.session.mode = "load";
	await runBridge(config, {
		...script([envelope([workAction("7ba67cb8-W164")])]),
		logger: quiet });
	const loaded = events(log).find((entry) => entry.event === "session/load");
	assert.equal(loaded.sessionId, born.sessionId,
		"continuity was assumed rather than proven: load used a different id");
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 2);
});

test("load without the capability fails closed before any session use", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_NO_LOAD: "1" } });
	config.session.mode = "load";
	seedSelection(config, "s-capability-probe");
	const warnings = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	assert.ok(warnings.some((line) => /loadSession capability/.test(line)));
	assert.ok(!events(log).some((entry) =>
		entry.event.startsWith("session/") || entry.event === "prompt/start"),
		"session use happened despite the missing capability");
});

test("an unsupported permission mode fails closed with no fallback", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_NO_BYPASS: "1" } });
	const warnings = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	assert.ok(warnings.some((line) =>
		/not among the agent's available modes/.test(line)),
		"the unsupported mode was not refused by name");
	assert.ok(!events(log).some((entry) => entry.event === "prompt/start"),
		"a prompt ran outside the required mode");
	assert.ok(!events(log).some((entry) => entry.event === "session/set_mode"),
		"the bridge fell back to selecting another mode");
});

test("missing policy resources refuse startup before the agent exists", () => {
	assert.throws(() => rig({
		policyResources: ["/nonexistent/prohibitions.json"],
	}), /policy resource .* missing or unreadable; refusing/);
});

test("malformed agent output is visible and retried without losing readiness", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_MALFORMED: "1" } });
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope(set);
			if (calls === 2) {
				delete config.agent.env.FAKE_ACP_MALFORMED;
				return envelope(set);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: { info() {}, warn(message) { warnings.push(message); } },
	});
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length >= 1, true,
		"readiness never reached the healthy agent");
	assert.equal(prompts.at(-1).text.includes("W163"), true);
});

// ---- W163 slice A round 2 ----

test("an unsupported mode keeps failing closed across repeated envelopes", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_NO_BYPASS: "1" } });
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	const { signal, runWait } = script([
		envelope(set), envelope(set), envelope(set),
	]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	const refusals = warnings.filter((line) =>
		/not among the agent's available modes/.test(line));
	assert.ok(refusals.length >= 3,
		`each retry must refuse anew, saw ${refusals.length}`);
	const inits = events(log).filter((entry) => entry.event === "initialize");
	assert.ok(inits.length >= 3,
		"a partial session was reused instead of killed and rebuilt");
	assert.ok(!events(log).some((entry) => entry.event === "prompt/start"),
		"a prompt ran through a half-initialized session");
	assert.ok(!events(log).some((entry) => entry.event === "session/set_mode"),
		"the bridge fell back to another mode on retry");
});

test("a missing load capability keeps failing closed across repeated envelopes", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_NO_LOAD: "1" } });
	config.session.mode = "load";
	seedSelection(config, "s-capability-retry");
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	const { signal, runWait } = script([envelope(set), envelope(set)]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	const refusals = warnings.filter((line) =>
		/loadSession capability/.test(line));
	assert.ok(refusals.length >= 2);
	assert.ok(!events(log).some((entry) =>
		entry.event.startsWith("session/") || entry.event === "prompt/start"),
		"session use happened on retry despite the missing capability");
});

test("policy configuration refuses absent, empty, blank and bad env forms", () => {
	const base = () => {
		const { config } = rig();
		return JSON.parse(JSON.stringify({
			baton: config.baton, agent: config.agent,
			runtime: config.runtime,
			session: config.session, permissionMode: config.permissionMode,
			policyResources: config.policyResources,
			stateDir: config.stateDir, retryMs: config.retryMs,
			turnTimeoutMs: config.turnTimeoutMs,
		}));
	};
	const absent = base();
	delete absent.policyResources;
	assert.throws(() => validateConfig(absent),
		/policyResources must name at least one/);
	const empty = base();
	empty.policyResources = [];
	assert.throws(() => validateConfig(empty),
		/policyResources must name at least one/);
	const blank = base();
	blank.policyResources = ["   "];
	assert.throws(() => validateConfig(blank),
		/non-empty path/);
	const missing = base();
	missing.policyResources = ["/nonexistent/prohibitions.json"];
	assert.throws(() => validateConfig(missing),
		/missing or unreadable; refusing/);
	const badEnv = base();
	badEnv.agent.env = { GOOD: "x", BAD: 7 };
	assert.throws(() => validateConfig(badEnv),
		/agent\.env\.BAD must be a string/);
});

test("an unreadable policy resource refuses before the agent spawns", (t) => {
	if (typeof process.getuid === "function" && process.getuid() === 0) {
		t.skip("root ignores file modes");
		return;
	}
	const { config, home } = rig();
	const locked = join(home, "locked-policy.json");
	writeFileSync(locked, "{}\n");
	chmodSync(locked, 0o000);
	const raw = {
		baton: config.baton, agent: config.agent,
		runtime: config.runtime,
		session: config.session, permissionMode: config.permissionMode,
		policyResources: [locked],
		stateDir: config.stateDir, retryMs: config.retryMs,
		turnTimeoutMs: config.turnTimeoutMs,
	};
	try {
		assert.throws(() => validateConfig(raw),
			/missing or unreadable; refusing/);
	} finally {
		chmodSync(locked, 0o644);
	}
});


test("a configured hard denial prevents the side effect without any prompt", async () => {
	const { log, config, home } = rig();
	const policy = join(home, "prohibitions.json");
	const sideEffect = join(home, "side-effect.txt");
	writeFileSync(policy, JSON.stringify({ denied: ["forbidden_tool"] }));
	config.policyResources = [policy];
	config.agent.env.FAKE_ACP_TRY_FORBIDDEN = "1";
	config.agent.env.FAKE_ACP_POLICY = policy;
	config.agent.env.FAKE_ACP_SIDE_EFFECT = sideEffect;
	const updates = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		onUpdate: (line) => updates.push(line) });
	assert.ok(events(log).some((entry) => entry.event === "tool/denied"),
		"the hard denial did not engage");
	assert.ok(!events(log).some((entry) => entry.event === "tool/ran"),
		"the prohibited operation ran");
	assert.throws(() => readFileSync(sideEffect),
		"the prohibited operation left a side effect");
	assert.ok(!events(log).some((entry) =>
		entry.event === "permission/outcome"),
		"a denial turned into an approval prompt");
	assert.ok(updates.some((line) => /forbidden_tool.*failed/.test(line)),
		"the denial was not visible on the foreground surface");
	assert.ok(events(log).some((entry) => entry.event === "prompt/end"),
		"the wake itself was lost to the denial");
});

test("a broken blocking policy fails closed without a side effect", async () => {
	const { log, config, home } = rig();
	const sideEffect = join(home, "side-effect.txt");
	config.agent.env.FAKE_ACP_TRY_FORBIDDEN = "1";
	config.agent.env.FAKE_ACP_POLICY = join(home, "no-such-policy.json");
	config.agent.env.FAKE_ACP_SIDE_EFFECT = sideEffect;
	const updates = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		onUpdate: (line) => updates.push(line) });
	assert.ok(events(log).some((entry) => entry.event === "hook/failure"),
		"the hook failure was invisible");
	assert.ok(!events(log).some((entry) => entry.event === "tool/ran"),
		"a broken policy allowed the prohibited operation");
	assert.throws(() => readFileSync(sideEffect),
		"the broken policy path left a side effect");
	assert.ok(updates.some((line) => /forbidden_tool.*failed/.test(line)),
		"the fail-closed refusal was not visible");
});

test("a mute agent hits the setup deadline visibly and recovery delivers", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_MUTE: "1" } });
	config.setupTimeoutMs = 300;
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope(set);
			if (calls === 2) {
				delete config.agent.env.FAKE_ACP_MUTE;
				return envelope(set);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: { info() {}, warn(message) { warnings.push(message); } },
	});
	assert.ok(warnings.some((line) =>
		/initialize did not complete within 300ms/.test(line)),
		"the unresponsive initialize was not deadlined by name");
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 1,
		"readiness did not reach the healthy agent after the mute one");
});

test("operator shutdown tears down an agent stuck mid-turn promptly", async () => {
	const { log, config } = rig({ env: { FAKE_ACP_NEVER_FINISH: "1" } });
	const controller = new AbortController();
	const run = runBridge(config, {
		signal: controller.signal,
		runWait: async () => envelope([workAction("7ba67cb8-W163")]),
		logger: quiet,
	});
	// wait until the turn is provably hung, then send the shutdown
	const started = Date.now();
	while (!events(log).some((entry) => entry.event === "prompt/hung")) {
		assert.ok(Date.now() - started < 5000, "the rig never hung");
		await new Promise((resolve) => setTimeout(resolve, 25));
	}
	const shutdownAt = Date.now();
	controller.abort();
	const code = await run;
	assert.equal(code, 0);
	assert.ok(Date.now() - shutdownAt < 3000,
		"shutdown waited on the unresponsive protocol call");
});

test("a missing agent executable is a visible spawn failure, retried", async () => {
	const { config } = rig();
	config.agent.command = "/nonexistent/acp-agent";
	config.setupTimeoutMs = 300;
	const warnings = [];
	const set = [workAction("7ba67cb8-W163")];
	const { signal, runWait } = script([envelope(set), envelope(set)]);
	await runBridge(config, { signal, runWait,
		logger: { info() {}, warn(message) { warnings.push(message); } } });
	const failures = warnings.filter((line) =>
		/could not deliver work:7ba67cb8-W163/.test(line));
	assert.ok(failures.length >= 2,
		"the missing executable was not retried visibly");
});

test("failed mode enforcement publishes no resumable session id", async () => {
	const { config } = rig({ env: { FAKE_ACP_NO_BYPASS: "1" } });
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	assert.throws(() => readFileSync(join(config.stateDir, "session.json")),
		/ENOENT/,
		"a session rejected before exact mode enforcement was published for later load");
});

// W27 (finding-acp-bootstrap-overwrites-session): session.mode=new MAKES
// a continuity context, so it is correct only when none exists yet. The
// live defect was a second bootstrap silently replacing the persisted
// selection before any Work was claimed, after which load resumed the
// wrong session. Rotation stays deliberately unimplemented.

// W49 (finding-acp-same-key-redelivery-loss): a queued prompt is an
// EDGE to re-evaluate, never authority to act from an old envelope.

test("episode revalidation is an immediate exact-key Baton read", async () => {
	const { config } = rig();
	const action = workAction("7ba67cb8-W27", { episode: 9, generation: 3 });
	const invocations = [];
	const live = await episodeStillLive(config, action, {
		execute: async (file, argv) => {
			invocations.push({ file, argv });
			return { stdout: JSON.stringify(envelope([action])) };
		},
	});
	// W11910 review [P1]: a VERDICT rather than a boolean. A boolean could
	// not say "still good, but another Work holds the claim slot", which is
	// neither delivery nor withdrawal.
	assert.equal(live, "live");
	assert.deepEqual(invocations, [{
		file: config.baton.binary,
		argv: ["--config", config.baton.config,
		       "--participant", config.baton.participant,
		       "wait", "timeout=0"],
	}], "pre-turn revalidation did not use the exact nonblocking wait");
	const stale = await episodeStillLive(config, action, {
		execute: async () => ({ stdout: JSON.stringify(envelope([
			workAction("7ba67cb8-W27", { episode: 10, generation: 3 }),
		])) }),
	});
	assert.equal(stale, "over",
		"a different episode of the same Work was accepted as still live");
});

test("the verdict separates a dead episode from one waiting on a claim",
async () => {
	// The three states the boolean could not express, from one envelope.
	const offer = workAction("7ba67cb8-W10265");
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	assert.equal(episodeVerdict(envelope([offer]), offer), "live");
	assert.equal(episodeVerdict(envelope([held]), offer), "over");
	assert.equal(episodeVerdict(envelope([held, offer]), offer), "deferred",
		"an offer waiting on another Work's claim was called live or dead");
	// A claimed Work is its OWN recovery and never waits behind itself.
	assert.equal(episodeVerdict(envelope([held]), held), "live");
	// And the one-claim Work slot does not govern anything that is not Work.
	const owed = { kind: "obligation", action_key: "obligation:9",
	               work: "7ba67cb8-W2", seq: 9 };
	assert.equal(episodeVerdict(envelope([held, owed]), owed), "live",
		"the Work claim-slot rule swallowed a non-Work action");
});

test("a Work neighbour with no claim verdict cannot answer that the slot is "
	+ "free", async () => {
	// W11910 fifth review [P1], on THIS side of the shared validator.
	//
	// The dispatcher's regression for this is `claim_slot.test.mjs`; the same
	// defect reached here by the same route, because `episodeVerdict` decides
	// deferral with `entry.claimed === true` and the validator used to accept
	// an absent `claimed`. A neighbour that is claimed but does not say so
	// therefore answered "the slot is free" about a slot it holds itself.
	//
	// The fix is in the validator both families import, so the assertion is
	// that the envelope never reaches the verdict at all: an unread claim bit
	// is an unreadable envelope, and the offer stays armed rather than
	// spending a turn on it.
	const offer = workAction("7ba67cb8-W10265");
	const { claimed, ...unread } = workAction("7ba67cb8-W6627",
	                                          { claimed: true });
	assert.throws(
		() => validateEnvelope(envelope([unread, offer]), "baton.claude"),
		/carries no claimed verdict/,
		"a Work with no claim verdict was accepted as a readable answer");
	// And the neighbour that DOES say so still defers the offer, so what the
	// case above rejects is the missing verdict rather than the shape.
	const held = workAction("7ba67cb8-W6627", { claimed: true });
	assert.equal(
		episodeVerdict(validateEnvelope(envelope([held, offer]),
		                                "baton.claude"), offer),
		"deferred");
});

test("a key answered under an unknown kind is unreadable, not withdrawn",
async () => {
	// W11910 re-review [P1]. The envelope contract is deliberately liberal
	// about kinds this build does not know: it drops them from the actionable
	// set and files them under `ignored_actions` so a newer authority can add
	// a primitive without breaking an older bridge. That tolerance is about
	// DELIVERY, and it says nothing about whether the episode is over.
	//
	// Driven through the REAL validator rather than a hand-built envelope,
	// because the ignored set is the contract's own output and a fixture that
	// invented it would prove nothing about the code that runs.
	const offer = workAction("7ba67cb8-W10265");
	const unknown = { kind: "escalation", action_key: offer.action_key,
	                  work: offer.work };
	const answered = validateEnvelope(envelope([unknown]), "baton.claude");
	assert.deepEqual(answered.result.actionable, [],
		"this fixture no longer exercises the tolerance it is about");
	assert.equal(episodeVerdict(answered, offer), "uncertain",
		"an entry this build cannot read was called an ended episode");
	// AND THE OTHER HALF: an answer that names the key nowhere at all is
	// still authoritative withdrawal, or retention would never let go.
	const gone = validateEnvelope(
		envelope([workAction("7ba67cb8-W6627")]), "baton.claude");
	assert.equal(episodeVerdict(gone, offer), "over",
		"a withdrawn episode was retained forever");
});

test("an offer answered under an unknown kind stays armed and spends no turn",
async () => {
	// End to end, and the same shape as a deferred offer: no prompt, no
	// withdrawal, no `markPresented` — so the very next poll offers it again
	// and it takes its turn once the authority answers in a kind this build
	// knows.
	const { config } = rig();
	const time = clock();
	const waiting = workAction("7ba67cb8-W10265");
	const { signal, runWait } = script([
		envelope([waiting]),
		() => {
			time.advance(config.retryMs * 8);
			return envelope([waiting]);
		},
	]);
	const trail = [];
	let checks = 0;
	await runBridge(config, {
		signal, runWait, now: time.now, logger: quiet,
		revalidate: async () => {
			const verdict = checks++ === 0 ? "uncertain" : "live";
			trail.push(verdict);
			return verdict;
		},
		sessionFactory: () => ({
			alive: () => true,
			sessionId: "sess-1",
			async start() { return "sess-1"; },
			async promptText() { trail.push("prompt"); },
			async stop() {},
		}),
	});
	assert.deepEqual(trail, ["uncertain", "live", "prompt"],
		"an unreadable answer either spent a turn or dropped a live offer");
});

test("a queued prompt whose episode ended is dropped before the agent turn", async () => {
	const { log, config } = rig();
	const action = workAction("7ba67cb8-W27");
	const { signal, runWait } = script([envelope([action])]);
	const infos = [];
	// the Work was claimed/passed/closed while this prompt sat queued:
	// the revalidation read no longer carries the exact episode key
	await runBridge(config, { signal, runWait,
		revalidate: async () => "over",
		logger: { info(message) { infos.push(message); }, warn() {} } });
	assert.ok(!events(log).some((entry) => entry.event === "prompt/start"),
		"a stale episode was presented to the agent as current work");
	assert.ok(infos.some((line) =>
		new RegExp(`${action.action_key} is no longer actionable`)
			.test(line)),
		"the drop was not reported by episode");
});

test("a stale drop does not resurrect: only a NEW episode redelivers", async () => {
	const { log, config } = rig();
	const dead = workAction("7ba67cb8-W27", { episode: 1 });
	const reborn = workAction("7ba67cb8-W27", { episode: 9 });
	let live = false;
	const { signal, runWait } = script([
		envelope([dead]),            // dropped: episode already over
		envelope([dead]),            // still the dead episode, still dropped
		envelope([reborn]),          // handed back: a genuinely new episode
	]);
	await runBridge(config, { signal, runWait,
		revalidate: async (action) => (action.episode_seq === 9 || live
			? "live" : "over"),
		logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 1,
		"the dead episode was retried, or the new one was suppressed");
	assert.match(prompts[0].text, /W27/);
});

test("revalidation passing delivers once, and the claim is what clears it",
async () => {
	// W11910 rewrote the second half of this case. It used to prove that
	// a still-live episode was suppressed after ONE returned prompt,
	// which is the defect stated as an assertion: a prompt that returned
	// without claiming leaves the Work ready and unclaimed. The delivery
	// property is unchanged — a live episode is handed over exactly once
	// — but what suppresses the repeat is the canonical claim.
	const { log, config } = rig();
	const offer = workAction("7ba67cb8-W163");
	const taken = workAction("7ba67cb8-W163", { claimed: true });
	const { signal, runWait } = script([envelope([offer]), envelope([taken])]);
	await runBridge(config, { signal, runWait,
		revalidate: async () => "live", logger: quiet });
	assert.equal(
		events(log).filter((entry) => entry.event === "prompt/start").length, 1,
		"a still-live episode was delivered more than once");
});

test("the first bootstrap creates and persists exactly one selection", async () => {
	const { log, config } = rig();
	await runBridge(config, {
		...script([envelope([workAction("7ba67cb8-W163")])]),
		logger: quiet });
	const born = events(log).filter((entry) => entry.event === "session/new");
	assert.equal(born.length, 1, "more than one session was created");
	const state = JSON.parse(
		readFileSync(join(config.stateDir, "session.json"), "utf8"));
	assert.equal(state.sessionId, born[0].sessionId,
		"the persisted selection is not the session that was created");
});

test("a repeated bootstrap refuses before any Baton wait or agent spawn", async () => {
	const { log, config } = rig();
	await runBridge(config, {
		...script([envelope([workAction("7ba67cb8-W163")])]),
		logger: quiet });
	const statePath = join(config.stateDir, "session.json");
	const survivor = readFileSync(statePath);
	const born = events(log).find((entry) => entry.event === "session/new");
	const before = events(log).length;

	// A SECOND bootstrap against the same state dir — the exact live
	// mistake (bootstrap.json where load.json was meant).
	let waits = 0;
	const second = script([envelope([workAction("7ba67cb8-W164")])]);
	await assert.rejects(
		() => runBridge(config, {
			signal: second.signal,
			runWait: () => { waits += 1; return second.runWait(); },
			logger: quiet }),
		/session\.mode=new but .*already selects session/,
		"the repeated bootstrap did not refuse by name");

	assert.equal(waits, 0, "the refused bootstrap still polled Baton");
	assert.equal(events(log).length, before,
		"the refused bootstrap still reached the ACP agent");
	assert.deepEqual(readFileSync(statePath), survivor,
		"the surviving selection was not preserved byte-for-byte");

	// And the original session is still the one that loads.
	config.session.mode = "load";
	await runBridge(config, {
		...script([envelope([workAction("7ba67cb8-W165")])]),
		logger: quiet });
	const loaded = events(log).find((entry) => entry.event === "session/load");
	assert.equal(loaded.sessionId, born.sessionId,
		"load resumed something other than the original session");
});

test("existing but unusable session state refuses both modes and survives", async () => {
	for (const [label, bytes] of [["malformed", "{not json"],
	                              ["empty selection", '{"sessionId":""}']]) {
		const { log, config } = rig();
		mkdirSync(config.stateDir, { recursive: true });
		const statePath = join(config.stateDir, "session.json");
		writeFileSync(statePath, bytes);

		await assert.rejects(
			() => runBridge(config, {
				...script([envelope([workAction("7ba67cb8-W163")])]),
				logger: quiet }),
			/already exists and is not a usable session selection/,
			`${label} state did not refuse the bootstrap by name`);
		assert.equal(readFileSync(statePath, "utf8"), bytes,
			`${label} state was not preserved`);
		assert.equal(events(log).length, 0,
			`${label} state still reached the ACP agent`);

		// load must not answer unusable state with "bootstrap a new one":
		// that advice is how a recoverable id gets discarded. W27 R2: it
		// refuses at STARTUP, with no Baton poll and no agent event.
		config.session.mode = "load";
		let waits = 0;
		const resume = script([envelope([workAction("7ba67cb8-W163")])]);
		await assert.rejects(
			() => runBridge(config, {
				signal: resume.signal,
				runWait: () => { waits += 1; return resume.runWait(); },
				logger: quiet }),
			(error) =>
				/not a usable session selection/.test(error.message)
				&& !/run a 'new' bootstrap/.test(error.message),
			`${label} state was not refused by name on load`);
		assert.equal(waits, 0, `${label} load still polled Baton`);
		assert.equal(events(log).length, 0,
			`${label} load still reached the ACP agent`);
		assert.equal(readFileSync(statePath, "utf8"), bytes,
			`${label} state was not preserved across the load attempt`);
	}
});

test("a load run with no persisted selection refuses at startup", async () => {
	// W27 R2 item 3: missing configured-load state is a launch mistake,
	// so it surfaces before the first poll rather than as a retry loop.
	const { log, config } = rig({ sessionMode: "load" });
	let waits = 0;
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await assert.rejects(
		() => runBridge(config, {
			signal, runWait: () => { waits += 1; return runWait(); },
			logger: quiet }),
		/no persisted session exists in .*run a 'new' bootstrap/s,
		"a load run without a selection did not refuse at startup");
	assert.equal(waits, 0, "the refused load run still polled Baton");
	assert.equal(events(log).length, 0,
		"the refused load run still reached the ACP agent");
});

test("a load run retains session A when the file changes to B mid-run", async () => {
	// W27 R2 item 4. One bridge run holds ONE continuity context. An
	// external edit — another bootstrap, an operator, a stale writer —
	// must not steer this run's replacement agent process onto a
	// different session, and this run must not rewrite what it found.
	const { log, config } = rig({ env: { FAKE_ACP_EXIT_ON_PROMPT: "1" },
	                              sessionMode: "load" });
	const statePath = join(config.stateDir, "session.json");
	seedSelection(config, "session-A");
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope([workAction("7ba67cb8-W163")]);
			if (calls === 2) {
				// the agent died on the first prompt; meanwhile the file
				// is repointed at a different session entirely
				delete config.agent.env.FAKE_ACP_EXIT_ON_PROMPT;
				seedSelection(config, "session-B");
				return envelope([workAction("7ba67cb8-W163")]);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: quiet,
	});
	const loaded = events(log).filter((entry) => entry.event === "session/load");
	assert.ok(loaded.length >= 2,
		"the replacement agent process never loaded");
	assert.deepEqual([...new Set(loaded.map((entry) => entry.sessionId))],
		["session-A"],
		"a rebuild reread the file and switched sessions mid-run");
	assert.equal(
		events(log).filter((entry) => entry.event === "session/new").length, 0,
		"a load run created a session");
	assert.equal(JSON.parse(readFileSync(statePath, "utf8")).sessionId,
		"session-B",
		"the load run rewrote the externally changed file");
});

test("agent-process death resumes the same session and never rotates it", async () => {
	// W27 R1. An agent PROCESS dying is not the ACP session dying: the
	// live W2 trial restarted the adapter and loaded the original
	// session with its context intact. So a replacement process must
	// LOAD the retained id — one session/new for the run, a load of
	// that identical id afterwards, and session.json untouched.
	// Creating a second session here would be a silent rotation
	// performed from inside the original bootstrap run.
	const { log, config } = rig({ env: { FAKE_ACP_EXIT_ON_PROMPT: "1" } });
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope([workAction("7ba67cb8-W163")]);
			if (calls === 2) {
				delete config.agent.env.FAKE_ACP_EXIT_ON_PROMPT;
				return envelope([workAction("7ba67cb8-W163")]);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: quiet,
	});
	const statePath = join(config.stateDir, "session.json");
	const born = events(log).filter((entry) => entry.event === "session/new");
	assert.equal(born.length, 1,
		"the replacement process created a second session instead of "
		+ "resuming the selected one");
	const loaded = events(log).filter((entry) => entry.event === "session/load");
	assert.equal(loaded.length, 1, "the replacement process did not load");
	assert.equal(loaded[0].sessionId, born[0].sessionId,
		"recovery loaded a different session than the one selected");
	const state = JSON.parse(readFileSync(statePath, "utf8"));
	assert.equal(state.sessionId, born[0].sessionId,
		"the selection was rewritten during ordinary operation");
	// and readiness still survived the crash
	assert.equal(
		events(log).filter((entry) => entry.event === "prompt/start").length, 2,
		"readiness was discarded by the crash instead of retried");
});

test("new and loaded ACP sessions receive accepted role instructions on their first readiness turn", async () => {
	for (const sessionMode of ["new", "load"]) {
		const { log, config } = rig({ participant: "baton.tuner", role: "tuner", sessionMode });
		if (sessionMode === "load") seedSelection(config, "retained-tuner-session");
		const wake = script([envelope([workAction("7ba67cb8-W101")], { participant: "baton.tuner" })]);
		await productionRunBridge(config, {
			signal: wake.signal,
			runWait: wake.runWait,
			logger: quiet,
			loadInstructions: async (source, identity) => {
				assert.equal(source.binary, "/unused/baton");
				assert.deepEqual(identity, config.baton);
				return { participant: "baton.tuner", role: "tuner",
				         instructions: "Own documentation and deployment polish.",
				         configurationGeneration: 3 };
			},
		});
		const prompts = events(log).filter((entry) => entry.event === "prompt/start");
		assert.equal(prompts.length, 1);
		assert.match(prompts[0].text, /Configured role instructions: Own documentation and deployment polish\./);
		assert.match(prompts[0].text,
			/^\[BATON READY\].*Apply standing v11 Baton policy\.$/m);
	}
});

// W101: "ambiguous" is no longer a reachable refusal — the role is always
// explicit — so this exercises the refusals that ARE reachable: a read that
// fails, and one naming a role the participant does not hold.
test("a refused ACP role-instruction read stops before wait or session use", async () => {
	const { log, config } = rig({ participant: "baton.tuner", role: "tuner" });
	let waits = 0;
	await assert.rejects(
		() => productionRunBridge(config, {
			runWait: async () => { waits += 1; return envelope([]); },
			logger: quiet,
			loadInstructions: async () => { throw new Error("participant baton.tuner does not hold role 'tuner'"); },
		}),
		/does not hold role/);
	assert.equal(waits, 0);
	assert.equal(events(log).length, 0);
});

test("recovery without the load capability refuses and creates nothing", async () => {
	// The fallback that must not exist: if the replacement process
	// cannot load, the bridge reports it and leaves readiness pending —
	// it never reaches for session/new to keep going.
	const { log, config } = rig({ env: { FAKE_ACP_EXIT_ON_PROMPT: "1" } });
	const warnings = [];
	let calls = 0;
	const controller = new AbortController();
	await runBridge(config, {
		signal: controller.signal,
		runWait: async () => {
			calls += 1;
			if (calls === 1) return envelope([workAction("7ba67cb8-W163")]);
			if (calls === 2) {
				// the replacement agent cannot resume
				delete config.agent.env.FAKE_ACP_EXIT_ON_PROMPT;
				config.agent.env.FAKE_ACP_NO_LOAD = "1";
				return envelope([workAction("7ba67cb8-W163")]);
			}
			controller.abort();
			const error = new Error("aborted");
			error.name = "AbortError";
			throw error;
		},
		logger: { info() {}, warn(message) { warnings.push(message); } },
	});
	const statePath = join(config.stateDir, "session.json");
	const survivor = JSON.parse(readFileSync(statePath, "utf8"));
	assert.ok(warnings.some((line) => /loadSession capability/.test(line)),
		"the unresumable replacement was not refused by name");
	const born = events(log).filter((entry) => entry.event === "session/new");
	assert.equal(born.length, 1,
		"the bridge fell back to creating a session it could not resume");
	assert.equal(survivor.sessionId, born[0].sessionId,
		"the selection did not survive the failed recovery");
	assert.equal(
		events(log).filter((entry) => entry.event === "session/load").length, 0,
		"a load was attempted despite the missing capability");
	// The refusal precedes any session use, so the only prompt is the
	// one the crash ate: readiness stays pending for a healthy agent
	// rather than being spent against a session that was never resumed.
	assert.equal(
		events(log).filter((entry) => entry.event === "prompt/start").length, 1,
		"a prompt ran after the recovery refusal");
});

test("publication is create-only: a racing winner is never replaced", async () => {
	const { config } = rig();
	const session = new AcpAgentSession(config, { logger: quiet });
	mkdirSync(config.stateDir, { recursive: true });
	const statePath = join(config.stateDir, "session.json");
	// The window the startup preflight cannot cover: another bridge
	// published between our preflight and our own write.
	const winner = '{\n  "sessionId": "winner-0001"\n}\n';
	writeFileSync(statePath, winner);
	assert.throws(() => session.persistSessionId("loser-0002"),
		/another bridge published .*while this bootstrap was creating/,
		"the create-only publication replaced the winner");
	assert.equal(readFileSync(statePath, "utf8"), winner,
		"the winning selection was not preserved byte-for-byte");
});

test("W101: the ACP launch configuration must name an explicit role", () => {
	// Every launcher names participant AND role. Inferring the role
	// meant a participant gaining a second role later silently changed
	// the persona of every session started for them, so a role-less
	// configuration is refused before any session is created or loaded.
	const base = () => {
		const { config } = rig();
		return JSON.parse(JSON.stringify({
			baton: config.baton, agent: config.agent,
			runtime: config.runtime,
			session: config.session, permissionMode: config.permissionMode,
			policyResources: config.policyResources,
			stateDir: config.stateDir, retryMs: config.retryMs,
			turnTimeoutMs: config.turnTimeoutMs,
		}));
	};
	const absent = base();
	delete absent.baton.role;
	assert.throws(() => validateConfig(absent), /baton\.role is required/);
	const blank = base();
	blank.baton.role = "   ";
	assert.throws(() => validateConfig(blank), /baton\.role is required/);
	const dotted = base();
	dotted.baton.role = "team.role";
	assert.throws(() => validateConfig(dotted), /baton\.role must be one role handle/);
	// and the ordinary form survives
	assert.equal(validateConfig(base()).baton.role, "impl");
});

// -- W93 slice 4: the runtime lease ------------------------------------------
//
// The ACP bridge drives turns directly, so it is the one adapter that
// knows WHICH assignment episode a runner is serving. It publishes that
// as correlation only: the Work table still decides who holds the
// claim, and a runtime report never claims, answers or completes
// anything.

// W55705: `incident` is part of the publisher the settlement uses, so the spy
// carries it. Additive: it answers true by default, records every row, and a
// case that is about a refused or thrown publication supplies its own answer.
function runtimeSpy({ incident = () => true } = {}) {
	const published = [];
	const incidents = [];
	return {
		published,
		incidents,
		runtime: {
			incarnation: "run-1",
			async start(options) { published.push(["start", options]); },
			async state(state, options) {
				published.push([state, options]);
			},
			async facts(supplied, options) {
				published.push(["facts", { ...supplied, ...options }]);
			},
			async end(options) { published.push(["end", options]); },
			async incident(row) {
				incidents.push(row);
				return await incident(row, incidents.length);
			},
		},
	};
}

test("the lease opens before the first wait and closes on the way out",
	async () => {
		const { config } = rig();
		const spy = runtimeSpy();
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime });
		assert.equal(spy.published[0][0], "start",
			JSON.stringify(spy.published));
		assert.equal(spy.published.at(-1)[0], "end");
	});

test("a delivered turn is working then idle, correlated to its episode",
	async () => {
		const { config } = rig();
		const spy = runtimeSpy();
		const action = workAction("7ba67cb8-W163");
		const { signal, runWait } = script([envelope([action])]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime });
		const states = spy.published.map(([state]) => state);
		const working = states.indexOf("working");
		assert.ok(working > 0, JSON.stringify(spy.published));
		assert.equal(states.indexOf("idle") > working, true,
			"idle did not follow the completed turn");
		const [, options] = spy.published[working];
		assert.equal(options.work, action.work);
		assert.equal(options.episode, action.episode_seq);
	});

test("a failed readiness read is retrying, never offline", async () => {
	const { config } = rig();
	const spy = runtimeSpy();
	let calls = 0;
	const controller = new AbortController();
	const runWait = async () => {
		calls += 1;
		// A realistic transport failure: the classification is honest,
		// so the message has to be one.
		if (calls === 1) throw new Error("connect ECONNREFUSED /run/baton.sock");
		controller.abort();
		const error = new Error("aborted");
		error.name = "AbortError";
		throw error;
	};
	await runBridge(config, { signal: controller.signal, runWait,
		logger: quiet, runtime: spy.runtime });
	const entry = spy.published.find(([state]) => state === "retrying");
	assert.ok(entry, JSON.stringify(spy.published));
	assert.equal(entry[1].cause, "transport");
	assert.ok(!spy.published.some(([state]) =>
		state === "offline" || state === "unknown"),
	"the bridge published a state only the authority derives");
});

test("a runtime publisher that fails never stops a delivery", async () => {
	// Diagnostics must not become an outage: the wake path is what the
	// agent is for, and a status line that cannot publish is a warning.
	const { log, config } = rig();
	const angry = {
		incarnation: null,
		async start() { throw new Error("no baton binary"); },
		async state() { throw new Error("no baton binary"); },
		async end() { throw new Error("no baton binary"); },
	};
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await assert.rejects(() => runBridge(config, { signal, runWait,
		logger: quiet, runtime: angry }));
	// The production publisher swallows its own failures, which is the
	// property that keeps the promise above; this proves the bridge
	// relies on it rather than guarding every call site.
	const { RuntimePublisher } = await import(
		"../../codex-event-bridge/src/runtime_publisher.mjs");
	const safe = new RuntimePublisher(
		{ binary: "/nonexistent", config: "/nonexistent",
		  participant: "lang.ada" },
		{ adapter: "acp", logger: quiet });
	assert.equal(await safe.start(), false);
	const second = script([envelope([workAction("7ba67cb8-W163")])]);
	await runBridge(config, { signal: second.signal,
		runWait: second.runWait, logger: quiet, runtime: safe });
	assert.ok(events(log).some((entry) => entry.event === "prompt/start"),
		"a failing runtime publisher blocked the delivery");
});

test("the deployment configuration validates runtime identity metadata",
	async () => {
		// The validator reads the policy resource, so the fixture owns
		// a real one — the point here is the runtime block, and the
		// surrounding refusals stay exactly as they are.
		const home = mkdtempSync(join(tmpdir(), "acp-runtime-config-"));
		const policy = join(home, "policy.md");
		writeFileSync(policy, "deployment-owned prohibitions\n");
		const base = {
			baton: { binary: "/opt/baton", config: "/opt/baton.json",
				participant: "lang.ada", role: "impl" },
			agent: { command: "/usr/bin/agent", cwd: home },
			session: { mode: "new", cwd: home },
			permissionMode: "bypassPermissions",
			policyResources: [policy],
			stateDir: join(home, "state"),
			turnTimeoutMs: 60000,
		};
		const ok = validateConfig({ ...base, runtime: {
			provider: "Anthropic", model: "claude-opus-5",
			actionOwner: "baton.slaw" } });
		assert.deepEqual(ok.runtime, { provider: "Anthropic",
			model: "claude-opus-5", actionOwner: "baton.slaw" });
		// Absent is refused — nothing is inferred from the agent command
		// or from the participant's name.
		assert.throws(() => validateConfig(base),
			/runtime\.actionOwner is required/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { actionOwner: "lang.ada" } }),
			/must differ from baton\.participant/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { actionOwner: "slaw" } }), /team\.member/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { provider: "", actionOwner: ACTION_OWNER } }), /non-empty/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { guessed: "x", actionOwner: ACTION_OWNER } }),
			/not a runtime metadata field/);
	});

test("a delivery failure is classified rather than called transport",
	async () => {
		const { config } = rig();
		const spy = runtimeSpy();
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, {
			signal, runWait, logger: quiet, runtime: spy.runtime,
			sessionFactory: () => ({
				alive: () => true,
				sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() {
					throw new Error("429 rate_limit_exceeded");
				},
				async stop() {},
			}),
		});
		const failure = spy.published.find(([state]) => state === "failed");
		assert.ok(failure, JSON.stringify(spy.published));
		assert.equal(failure[1].cause, "limit");
		assert.doesNotMatch(failure[1].detail, /429|rate_limit_exceeded/,
			"the upstream message was persisted as runtime detail");
	});

test("a clean bridge exit carries no failure cause", async () => {
	const { config } = rig();
	const spy = runtimeSpy();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		runtime: spy.runtime });
	const [, options] = spy.published.at(-1);
	assert.equal(options?.cause, undefined,
		"a clean shutdown was reported as a failure");
});

// -- W93 slice 6: the inventory and the refresh signal ------------------------

test("the production startup path publishes the facts it actually knows",
	async () => {
		// R17: not the publisher method called in isolation — the real
		// runBridge startup, which is where a deployed runner either
		// gets an inventory or does not.
		const { config } = rig();
		const spy = runtimeSpy();
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime });
		const published = spy.published.find(([kind]) => kind === "facts");
		assert.ok(published, JSON.stringify(spy.published));
		const [, sent] = published;
		assert.match(sent.service, /acp-baton-bridge pid \d+/);
		assert.equal(sent.workdir, config.agent.cwd);
		assert.equal(sent.readiness, config.baton.config);
		assert.equal(sent.source, "configured");
		// Nothing it cannot observe is guessed.
		assert.equal(sent.version, undefined);
		assert.equal(sent.dispatcher, undefined);
	});

test("a refresh request is answered from held facts and never delivered",
	async () => {
		// R18: level-triggered, adapter-visible, and NOT a model turn.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const refresh = {
			kind: "runtime_refresh",
			// R25: keyed on the GENERATION, which is also what the
			// adapter answers.
			action_key: "runtime-refresh:run-1:7",
			incarnation: "run-1",
			generation: 7,
			requested_at: "2026-08-19T11:00:00Z",
			wakes_model: false,
		};
		const { signal, runWait } = script([envelope([refresh])]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime });
		const facts = spy.published.filter(([kind]) => kind === "facts");
		assert.equal(facts.length, 2,
			"the refresh did not produce a second publication");
		assert.equal(facts.at(-1)[1].answers, 7,
			"the publication answered no particular request");
		assert.ok(!events(log).some((entry) =>
			entry.event === "prompt/start"),
		"a refresh request was forwarded to the agent");
	});

test("a redelivered refresh is answered again", async () => {
	// Level-triggered: the request stands until a publication clears
	// it, so a lost delivery simply reappears and is answered again.
	const { config } = rig();
	const spy = runtimeSpy();
	const refresh = {
		kind: "runtime_refresh",
		action_key: "runtime-refresh:run-1:7",
		incarnation: "run-1",
		generation: 7,
		requested_at: "2026-08-19T11:00:00Z",
		wakes_model: false,
	};
	const { signal, runWait } = script([
		envelope([refresh]), envelope([refresh]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		runtime: spy.runtime });
	const facts = spy.published.filter(([kind]) => kind === "facts");
	assert.equal(facts.length, 3, JSON.stringify(spy.published));
});

test("an envelope carrying a refresh must declare it wakes no model",
	async () => {
		const { validateEnvelope } = await import(
			"../src/baton_readiness.mjs");
		const bad = envelope([{
			kind: "runtime_refresh",
			action_key: "runtime-refresh:run-1:x",
			incarnation: "run-1",
			generation: 7,
			wakes_model: true,
		}]);
		assert.throws(() => validateEnvelope(bad, "baton.claude"),
			/wakes_model/);
	});

// -- W28681: the managed tool-process lifetime -------------------------------
//
// The incident: a managed turn published `working` for the better part of an
// hour while five tool process groups it had left behind survived 34-36 hours,
// one of them holding a full core. Four of them had called `setsid`, so they
// were not in the bridge's process group or session at all. The turn itself
// had no deadline — `promptText` raced only the agent's death — and a healthy
// agent process was RETAINED across turns, so nothing could correlate a
// surviving child with the turn that made it, let alone destroy it.
//
// The ruled boundary has three parts and these cases are written to them:
// a mandatory wall-clock turn deadline that is deployment policy rather than
// a repository guess; ONE process domain per delivered turn, destroyed and
// PROVED gone before anything is settled; and a teardown that cannot be proved
// fencing the lane instead of being assumed.

test("W28681: the turn deadline is mandatory configuration with no default",
	() => {
		// EVERY other timeout here has a default because a wrong guess is
		// merely slow. A wrong guess HERE either kills legitimate long work
		// or leaves this defect open, so an undecided deployment does not
		// start.
		const { config } = rig();
		const base = JSON.parse(JSON.stringify({
			baton: config.baton, agent: config.agent,
			runtime: config.runtime,
			session: config.session, permissionMode: config.permissionMode,
			policyResources: config.policyResources,
			stateDir: config.stateDir, retryMs: config.retryMs,
		}));
		assert.throws(() => validateConfig(base),
			/turnTimeoutMs must be a positive integer/);
		for (const bad of [0, -1, 1.5, "60000", null, Number.NaN,
		                   Number.MAX_SAFE_INTEGER + 2]) {
			assert.throws(
				() => validateConfig({ ...base, turnTimeoutMs: bad }),
				/turnTimeoutMs must be a positive integer/,
				`turnTimeoutMs ${JSON.stringify(bad)} was accepted`);
		}
		assert.equal(validateConfig({ ...base, turnTimeoutMs: 1 })
			.turnTimeoutMs, 1);
	});

test("W28681: a deadline this runtime cannot hold is refused", () => {
	// Review [P1]: every positive safe integer was accepted, and a Node timer
	// interval is a SIGNED 32-BIT millisecond value. `2147483648` validated,
	// `setTimeout` warned about the overflow, and the deadline became ONE
	// MILLISECOND — the longest an operator can express turning into the
	// shortest there is, without a refusal anywhere.
	//
	// REFUSED RATHER THAN CLAMPED: clamping would substitute this
	// repository's number for the operator's, which is exactly what giving
	// this operand no default was for.
	const { config } = rig();
	const base = JSON.parse(JSON.stringify({
		baton: config.baton, agent: config.agent,
		runtime: config.runtime,
		session: config.session, permissionMode: config.permissionMode,
		policyResources: config.policyResources,
		stateDir: config.stateDir, retryMs: config.retryMs,
	}));
	assert.equal(MAX_TURN_TIMEOUT_MS, 2147483647);
	// THE EXACT BOUNDARY, both sides.
	assert.equal(
		validateConfig({ ...base, turnTimeoutMs: MAX_TURN_TIMEOUT_MS })
			.turnTimeoutMs, MAX_TURN_TIMEOUT_MS);
	assert.throws(
		() => validateConfig({ ...base,
			turnTimeoutMs: MAX_TURN_TIMEOUT_MS + 1 }),
		/at most 2147483647 milliseconds/);
	assert.throws(
		() => validateConfig({ ...base,
			turnTimeoutMs: Number.MAX_SAFE_INTEGER }),
		/at most 2147483647 milliseconds/);
	// AND THE CEILING IS THE RUNTIME'S OWN, measured rather than asserted
	// about: one past it is the value Node truncates.
	const overflowed = [];
	const warn = process.emitWarning;
	process.emitWarning = (message, ...rest) => {
		overflowed.push(String(message));
		return warn.call(process, message, ...rest);
	};
	const timer = setTimeout(() => {}, MAX_TURN_TIMEOUT_MS + 1);
	clearTimeout(timer);
	process.emitWarning = warn;
	assert.ok(overflowed.some((one) => /TimeoutOverflow|does not fit/i
		.test(one)),
		"this runtime no longer truncates past the pinned ceiling; "
		+ "re-derive MAX_TURN_TIMEOUT_MS rather than leaving it a guess");
});

test("W28681: a turn that never returns hits its deadline and ends", async () => {
	// The defect, driven. Without the deadline this case does not finish:
	// the fake agent's prompt returns a promise that never settles and the
	// agent stays perfectly healthy, which is exactly the state the incident
	// found projected as `working` for an hour.
	const { config } = rig({ env: { FAKE_ACP_NEVER_FINISH: "1" },
	                         turnTimeoutMs: 150 });
	const spy = runtimeSpy();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
	                          runtime: spy.runtime });
	const failed = spy.published.filter(([state]) => state === "failed");
	assert.ok(failed.length >= 1, "the deadline published no failure");
	assert.equal(failed[0][1].cause, "internal");
	assert.match(failed[0][1].detail, /turn deadline exceeded/);
	// THE CORRELATION SURVIVES: which assignment held the lane until it
	// timed out is the whole operator question.
	assert.equal(failed[0][1].work, "7ba67cb8-W163");
	assert.equal(failed[0][1].episode, 1);
	// AND NO `idle` WAS PUBLISHED for a turn that did not finish.
	const idleBeforeFailure = spy.published
		.slice(0, spy.published.indexOf(failed[0]))
		.some(([state]) => state === "idle");
	assert.equal(idleBeforeFailure, false,
		"a timed-out turn reported itself idle");
});

test("W28681: streamed updates never extend the deadline", async () => {
	// A watchdog that reset on ACP activity would keep this turn alive
	// forever: the agent is hung AND talking. The bound is wall-clock, so
	// the chatter is a diagnostic and nothing more.
	const { config, log } = rig({
		env: { FAKE_ACP_NEVER_FINISH: "1", FAKE_ACP_CHATTY_MS: "20" },
		turnTimeoutMs: 200 });
	const spy = runtimeSpy();
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	const seen = [];
	await runBridge(config, { signal, runWait, logger: quiet,
	                          runtime: spy.runtime,
	                          onUpdate: (line) => seen.push(line) });
	// THE ACTIVITY WAS REAL, and that assertion is the case. Review [P1]:
	// the first version emitted an update missing `toolCallId`, the SDK
	// refused every one, and the deadline was reached over a SILENT agent —
	// so the case proved the timer worked and nothing about whether streamed
	// activity extends it.
	const beats = events(log).filter((one) => one.event === "tool/update");
	const refused = events(log).filter(
		(one) => one.event === "tool/update-refused");
	assert.equal(refused.length, 0,
		`the agent's updates were refused: ${JSON.stringify(refused[0])}`);
	assert.ok(beats.length >= 2,
		"the agent never streamed a valid update, so nothing was extended");
	assert.ok(seen.length >= 1, "no update reached the bridge's handler");
	// AND THE DEADLINE STILL ENDED IT.
	assert.ok(spy.published.some(([state, options]) =>
		state === "failed" && /turn deadline exceeded/.test(options.detail)),
		"a talkative infinite turn outlived its deadline");
	assert.ok(events(log).some((one) => one.event === "prompt/hung"));
});

test("W28681: the domain is destroyed before a delivered turn is settled",
	async () => {
		// A prompt that RETURNED says the model stopped talking. It says
		// nothing about what its tools left running, so `idle` must not be
		// published beside a domain that is still alive.
		const { config } = rig();
		const spy = runtimeSpy();
		const stops = [];
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime,
			sessionFactory: (cfg, hooks) => {
				const session = new AcpAgentSession(cfg, hooks);
				const real = session.stop.bind(session);
				session.stop = async () => {
					stops.push(spy.published.map(([state]) => state));
					return await real();
				};
				return session;
			} });
		assert.ok(stops.length >= 1, "the domain was never torn down");
		// THE ORDER IS THE ASSERTION: at the first teardown, `working` had
		// been published and `idle` had not.
		assert.ok(stops[0].includes("working"));
		assert.equal(stops[0].includes("idle"), false,
			"idle was published before the domain was destroyed");
		assert.ok(spy.published.some(([state]) => state === "idle"),
			"the delivered turn never reported idle");
	});

test("W28681: one process domain serves at most one delivered turn", async () => {
	// ACP session continuity is not PROCESS continuity: the run retains one
	// session id and the replacement resumes it. That is what makes a
	// per-turn domain legal, and it is what the incident's retained agent
	// process was trading away.
	const { config, log } = rig({ sessionMode: "new" });
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
		envelope([workAction("7ba67cb8-W164")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet });
	const seen = events(log);
	const created = seen.filter((one) => one.event === "session/new");
	const loaded = seen.filter((one) => one.event === "session/load");
	// TWO TURNS, TWO PROCESSES, ONE SESSION. The first bootstraps and the
	// second resumes exactly what the first published — never a rotation.
	assert.equal(created.length, 1, "a replacement process created a session");
	assert.equal(loaded.length, 1, "the replacement did not resume");
	assert.equal(loaded[0].sessionId, created[0].sessionId);
	assert.equal(seen.filter((one) => one.event === "prompt/start").length, 2);
});

test("W28681: a failed turn destroys its domain before it is reported",
	async () => {
		// A turn that failed left exactly the descendants a turn that
		// succeeded would have. Reporting first would publish a settlement
		// beside a live domain.
		const { config } = rig({ env: { FAKE_ACP_PERMISSION: "1" } });
		const spy = runtimeSpy();
		const stops = [];
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163")]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime,
			sessionFactory: (cfg, hooks) => {
				const session = new AcpAgentSession(cfg, hooks);
				const real = session.stop.bind(session);
				session.stop = async () => {
					stops.push(spy.published.map(([state]) => state));
					return await real();
				};
				return session;
			} });
		const failed = spy.published.filter(([state]) => state === "failed");
		assert.ok(failed.length >= 1);
		assert.ok(stops.some((before) => !before.includes("failed")),
			"every teardown happened after the failure was already reported");
	});

test("W28681: a teardown that cannot be proved fences the lane", async () => {
	// THE FAIL-CLOSED CASE. Everything after an unprovable teardown would be
	// built on an assumption about a process that may still be running, so
	// there is no `idle`, no acknowledgement of the offer, and no
	// replacement domain — the delivery lane stops instead.
	const { config } = rig();
	const spy = runtimeSpy();
	const abandoned = [];
	let built = 0;
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await assert.rejects(runBridge(config, { signal, runWait, logger: quiet,
		runtime: spy.runtime,
		sessionFactory: (cfg, hooks) => {
			built += 1;
			const session = new AcpAgentSession(cfg, hooks);
			abandoned.push(session);
			session.stop = async () => {
				session.ready = false;
				throw new DomainTeardownError(
					"the ACP agent process domain did not exit");
			};
			return session;
		} }), /did not exit/);
	// THE FIXTURE CLEANS UP WHAT THE BRIDGE CORRECTLY REFUSED TO. A domain
	// this bridge could not prove gone is one it leaves alone, so the real
	// subprocess is still alive here — which is the assertion, and also why
	// this suite has to reap it rather than leak it into the runner.
	for (const one of abandoned) one.child?.kill("SIGKILL");
	assert.equal(built, 1, "a replacement domain was started anyway");
	const failed = spy.published.filter(([state]) => state === "failed");
	assert.ok(failed.length >= 1);
	assert.equal(failed[0][1].cause, "internal");
	assert.match(failed[0][1].detail, /could not prove/);
	assert.match(failed[0][1].detail, /fenced/);
	assert.equal(spy.published.some(([state]) => state === "idle"), false,
		"an unprovable teardown still reported idle");
});

test("W28681: an unprovable exit is a refusal rather than an unbounded wait",
	async () => {
		// The old teardown awaited the child's exit after SIGKILL with no
		// bound at all, which is the same shape as the defect one layer
		// down: a supervisor that can hang inside its own recovery. This
		// drives a session whose child never reports an exit.
		const { config } = rig();
		const session = new AcpAgentSession(config, { logger: quiet });
		session.child = { pid: 424242, exitCode: null, kill() {} };
		session.exited = new Promise(() => {});
		session.ready = true;
		const started = Date.now();
		await assert.rejects(session.stop(), /cannot be proved/);
		// Bounded, and the bound is this supervisor's own rather than a
		// fifth timeout an operator has to reason about.
		assert.ok(Date.now() - started < 30000);
	});

test("W28681: operator shutdown destroys the last domain", async () => {
	const { config } = rig();
	const stops = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		sessionFactory: (cfg, hooks) => {
			const session = new AcpAgentSession(cfg, hooks);
			const real = session.stop.bind(session);
			session.stop = async () => { stops.push(1); return await real(); };
			return session;
		} });
	assert.ok(stops.length >= 1);
});

test("W28681: a tool descendant that escaped to its own session", async (t) => {
	// THE INCIDENT'S EXACT SHAPE, driven against real processes: a tool
	// child that made itself a session leader, which is what all four
	// surviving polling shells had done.
	//
	// WHAT THIS CASE CAN AND CANNOT ESTABLISH is the point of its two
	// halves. The bridge destroying its direct child is portable and is
	// asserted unconditionally. Whether that reaches a `setsid` descendant
	// depends on the configured launcher being a PID namespace, which is a
	// property of the LAUNCH CONTEXT -- this suite runs inside a managed
	// sandbox that cannot create one, and a case that silently passed here
	// would be claiming a boundary it never crossed.
	const home = mkdtempSync(join(tmpdir(), "acp-descendant-"));
	const pidFile = join(home, "descendant.pid");
	const { config } = rig({ env: { FAKE_ACP_LEAVE_DESCENDANT: pidFile } });
	const sessions = [];
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163")]),
	]);
	await runBridge(config, { signal, runWait, logger: quiet,
		sessionFactory: (cfg, hooks) => {
			const session = new AcpAgentSession(cfg, hooks);
			sessions.push(session);
			return session;
		} });
	// THE PORTABLE HALF: the domain owner is gone, proved by the exit this
	// bridge waited for rather than by a later look at the process table.
	assert.ok(sessions.length >= 1);
	for (const one of sessions) {
		assert.notEqual(one.child?.exitCode ?? "gone", null,
			"the agent process was left running after the turn");
	}
	const descendant = Number(readFileSync(pidFile, "utf8").trim());
	assert.ok(Number.isInteger(descendant) && descendant > 1);
	// THE HALF THAT NEEDS A DOMAIN. Reported either way rather than hidden:
	// a skip that names its reason is evidence, and a green assertion that
	// never ran is not.
	let contained;
	try {
		process.kill(descendant, 0);
		contained = false;
	} catch {
		contained = true;
	}
	if (!contained) {
		// Reap what this environment could not contain, then say so.
		try { process.kill(descendant, "SIGKILL"); } catch { /* gone */ }
		t.diagnostic("this environment gave the agent no PID namespace, so a "
			+ "setsid descendant survived the turn -- which is the defect, and "
			+ "is why the configured launcher must pass --unshare-pid; run "
			+ "preflight-process-domain.sh in the service launch context");
	}
});

test("W28681: a later failure never names the preceding action's episode",
	async () => {
		// Re-review [P1]: `correlation` lived outside the per-action loop and
		// was set only after `ensureSession()` succeeded. So after one
		// DELIVERED action, a later one failing during revalidation or
		// replacement setup published the FIRST action's work, episode and
		// session — affirmative operator evidence pointing at the wrong
		// assignment, which is worse than the uncorrelated failure these
		// paths produced before this Work existed.
		const { config } = rig();
		const spy = runtimeSpy();
		let built = 0;
		// ONE ENVELOPE, TWO ACTIONS. That is the shape the defect needs and
		// the shape my first version of this case got wrong: `correlation`
		// was declared per ENVELOPE, so two actions in two envelopes each got
		// a fresh one and the case passed against the broken code. Measured
		// against the pre-fix source before being trusted.
		// ONE ENVELOPE, TWO ACTIONS, and the second is a POKE. That is the
		// shape the defect needs, and it is the shape my first version of
		// this case got wrong twice: `correlation` was declared per ENVELOPE,
		// so two actions in two envelopes each got a fresh one; and two WORK
		// actions do not both deliver, because the second waits behind the
		// first's claim slot. A poke delivers beside Work and carries no work
		// or episode of its own — so anything it publishes came from
		// somewhere else. Measured against the pre-fix source before being
		// trusted.
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163", { episode: 1 }),
			          pokeAction(9)]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet,
			runtime: spy.runtime,
			sessionFactory: (cfg, hooks) => {
				built += 1;
				const session = new AcpAgentSession(cfg, hooks);
				if (built > 1) {
					// The REPLACEMENT domain cannot be established. Nothing
					// about the second action ever reaches a session, so the
					// bridge knows no session id for it — and must not borrow
					// the first one's.
					session.start = async () => {
						throw new Error("replacement setup failed");
					};
				}
				return session;
			} });
		const failed = spy.published.filter(([state]) => state === "failed");
		assert.ok(failed.length >= 1, "the second action reported no failure");
		for (const [, options] of failed) {
			assert.equal(options.work ?? null, null,
				"a failure named a Work it did not serve");
			assert.equal(options.episode ?? null, null,
				"a failure named an episode it did not serve");
			assert.equal(options.session ?? null, null,
				"a failure named a session it never had");
		}
		// AND THE FIRST DELIVERY WAS REAL, so this is not passing because
		// nothing happened.
		assert.ok(spy.published.some(([state, options]) =>
			state === "working" && options.work === "7ba67cb8-W163"));
		assert.ok(spy.published.some(([state]) => state === "idle"));
	});

// -- W55705: the post-turn canonical claim settlement -------------------------
//
// `work/records/2026/08/finding-acp-turn-teardown-strands-live-worker/`.
//
// THE INCIDENT, twice. `baton.claude` claimed W51487, launched a retained
// dogfood attempt, and the ACP delivery ended. The bridge proved its process
// domain gone, published `idle`, and marked the offer presented — while
// canonical state still recorded the Work `active` under that participant at
// that episode and the delegated container was still running with no
// supervising turn. Three published facts, none agreeing, and no incident.
//
// WHAT THESE ASSERT, and it is deliberately not "the runtime methods were
// called": the canonical read DECIDES, and the three verdicts it produces —
// released, recoverable, stranded — are each proved end to end through
// `runBridge` and then in isolation at the state machine, including every way
// the read, the marker and the incident publication can fail.

const OTHER_UUID = "1c1c1c1c1c1c4d4d8e8e0f0f0f0f0f0f";

/** The canonical `wait timeout=0` answer the settlement reads. */
function slot(entries, { uuid = UUID } = {}) {
	return { protocol_version: 11, projection_version: "12.0",
	         participant: "baton.claude", authority_uuid: uuid,
	         snapshot_seq: 43,
	         result: { actionable: entries, timed_out: false } };
}

/** A settlement wired to a scripted sequence of canonical answers.
 *
 *  A step may be an envelope, a thunk, or an `Error` to throw; the last step
 *  repeats, so a case names only the answers it cares about. `reads` is the
 *  live array, so a case can append to it after construction.
 */
function settlementFor(config, { spy, reads, now, store }) {
	let at = 0;
	return new AcpSettlement(config, {
		runtime: spy.runtime, logger: quiet, now, store,
		readSlot: async () => {
			const step = reads[Math.min(at, reads.length - 1)];
			at += 1;
			if (typeof step === "function") return await step();
			if (step instanceof Error) throw step;
			return step;
		},
	});
}

function focused({ reads = [], incident = () => true, store,
                   config: supplied } = {}) {
	const config = supplied ?? rig().config;
	const spy = runtimeSpy({ incident });
	const time = clock();
	const settle = settlementFor(config, { spy, reads, now: time.now, store });
	return { config, spy, settle, time, reads };
}

/** A store whose persistence can be made to fail, one call at a time. */
function scriptedStore({ onSave = () => true, onClear = () => true,
                         initial = { state: "absent" } } = {}) {
	const saved = [];
	let held = initial;
	return {
		saved,
		current: () => held,
		load() { return held; },
		preserveDamaged() { return "/tmp/preserved.damaged"; },
		save(_participant, _key, record) {
			saved.push(record);
			const ok = onSave(record, saved.length);
			if (ok) held = { state: "present", record };
			return ok;
		},
		clear() {
			const ok = onClear();
			if (ok) held = { state: "absent" };
			return ok;
		},
	};
}

const CLAIM_SLOT_KEY = (participant) => quarantineKey(participant, "acp-claim");

// -- the three verdicts, end to end through runBridge ------------------------

test("W55705: a returned prompt with no surviving claim is idle and presented",
	async () => {
		// The ordinary turn, and it must stay ordinary: a canonical read that
		// answers "no claim" is the ONLY thing that earns `idle`.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const { signal, runWait } = script([envelope([action])]);
		const settlement = settlementFor(config,
			{ spy, reads: [slot([])], now: time.now });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		const states = spy.published.map(([state]) => state);
		assert.ok(states.includes("idle"), JSON.stringify(spy.published));
		assert.ok(!states.includes("failed"), JSON.stringify(spy.published));
		assert.equal(spy.incidents.length, 0,
			"an incident was filed for a slot nobody held");
		assert.equal(
			events(log).filter((e) => e.event === "prompt/start").length, 1);
	});

test("W55705: a returned prompt whose exact claim survives is failed, never idle",
	async () => {
		// THE OBSERVED DEFECT, as one case. The pre-turn read saw a free slot
		// and the post-turn read sees the participant holding the delivered
		// assignment — which is exactly run7 — and the bridge must publish
		// `failed` with that Work named plus ONE durable incident, rather than
		// advertising capacity it does not have.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W51487", { episode: 55530 });
		const surviving = workAction("7ba67cb8-W51487",
			{ episode: 55530, claimed: true });
		const { signal, runWait } = script([envelope([action])]);
		const settlement = settlementFor(config,
			{ spy, reads: [slot([surviving])], now: time.now });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		const states = spy.published.map(([state]) => state);
		assert.ok(!states.includes("idle"),
			`idle was published beside a surviving claim: `
			+ JSON.stringify(spy.published));
		const failure = spy.published.find(([state]) => state === "failed");
		assert.ok(failure, JSON.stringify(spy.published));
		assert.equal(failure[1].cause, "internal");
		assert.equal(failure[1].work, "7ba67cb8-W51487");
		assert.equal(failure[1].episode, 55530);
		assert.equal(spy.incidents.length, 1, "the operator got no notice");
		assert.equal(spy.incidents[0].work, "7ba67cb8-W51487");
		assert.equal(spy.incidents[0].episode, 55530);
		assert.match(spy.incidents[0].detail, /still holds an active claim/);
	});

test("W85873: a returned poke over a pre-existing claim is failed, never idle",
	async () => {
		// THE RECURRENCE, not the neighboring-poke shape covered below. The
		// delivered action itself is a poke and carries no Work identity; an
		// independent post-turn canonical read still sees W85500 in this
		// participant's claim slot. Settlement is action-kind neutral, so that
		// live claim decides the runtime state and incident.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const poke = pokeAction(85773);
		const surviving = workAction("7ba67cb8-W85500",
			{ episode: 85563, claimed: true });
		const { signal, runWait } = script([envelope([poke])]);
		const settlement = settlementFor(config,
			{ spy, reads: [slot([surviving])], now: time.now });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		const prompts = events(log).filter((entry) =>
			entry.event === "prompt/start");
		assert.equal(prompts.length, 1, "the poke turn did not run exactly once");
		assert.match(prompts[0].text, /poke-answer poke=85773/);
		assert.ok(!spy.published.some(([state]) => state === "idle"),
			`idle was published beside a surviving claim: `
			+ JSON.stringify(spy.published));
		const failure = spy.published.find(([state]) => state === "failed");
		assert.ok(failure, JSON.stringify(spy.published));
		assert.equal(failure[1].cause, "internal");
		assert.equal(failure[1].work, "7ba67cb8-W85500");
		assert.equal(failure[1].episode, 85563);
		assert.equal(settlement.fence.correlation, "held");
		assert.equal(settlement.fence.work, "7ba67cb8-W85500");
		assert.equal(settlement.fence.episode, 85563);
		assert.equal(spy.incidents.length, 1,
			"the surviving claim produced no actionable incident");
		assert.equal(spy.incidents[0].work, "7ba67cb8-W85500");
		assert.equal(spy.incidents[0].episode, 85563);
	});

test("W85873: repeated pokes stay fenced across restart until canonical release",
	async () => {
		// First process: a poke returns over a claim and persists one held fence.
		// Second process: a later poke is retained while that claim survives,
		// then is delivered normally after an exact canonical read proves the
		// slot free. No poke replays, releases, accepts or transfers the Work.
		const { log, config } = rig();
		const firstSpy = runtimeSpy();
		const firstTime = clock();
		const firstPoke = pokeAction(85773);
		const held = workAction("7ba67cb8-W85500",
			{ episode: 85563, claimed: true });
		const firstFeed = script([envelope([firstPoke])]);
		const firstSettlement = settlementFor(config, {
			spy: firstSpy, reads: [slot([held])], now: firstTime.now });
		await runBridge(config, { signal: firstFeed.signal,
			runWait: firstFeed.runWait, logger: quiet, now: firstTime.now,
			runtime: firstSpy.runtime, settlement: firstSettlement });
		assert.equal(firstSpy.incidents.length, 1);
		assert.ok(!firstSpy.published.some(([state]) => state === "idle"));

		config.session.mode = "load";
		const secondSpy = runtimeSpy();
		const secondTime = clock(2_000_000);
		const nextPoke = pokeAction(85774);
		const secondFeed = script([
			envelope([nextPoke]),
			() => {
				secondTime.advance(RECONCILE_MS + 1);
				return envelope([nextPoke]);
			},
		]);
		const secondSettlement = settlementFor(config, {
			spy: secondSpy, reads: [slot([held]), () => {
				assert.ok(!secondSpy.published.some(([state]) => state === "idle"),
					"restart published idle before canonical release");
				return slot([]);
			}, slot([])],
			now: secondTime.now });
		await runBridge(config, { signal: secondFeed.signal,
			runWait: secondFeed.runWait, logger: quiet, now: secondTime.now,
			runtime: secondSpy.runtime, settlement: secondSettlement });
		const prompts = events(log).filter((entry) =>
			entry.event === "prompt/start");
		assert.equal(prompts.length, 2,
			"the repeated poke ran while held or failed to resume after release");
		assert.match(prompts[0].text, /poke-answer poke=85773/);
		assert.match(prompts[1].text, /poke-answer poke=85774/);
		assert.equal(secondSpy.incidents.length, 0,
			"restart duplicated the already-filed incident");
		assert.ok(secondSpy.published.some(([state]) => state === "idle"),
			"ordinary poke delivery did not resume after canonical release");
		assert.equal(secondSettlement.restore().state, "absent",
			"the released claim left a restart fence behind");
	});

test("W55705: a failed prompt whose exact claim survives is delivered again",
	async () => {
		// THE W11910 SPLIT, pinned in the finding as the approved scheduling
		// refinement. A recovery prompt that FAILED before returning left an
		// UNSPENT wake: suppressing it would leave a live claim with no retry
		// until somebody restarted the process, which is the exact
		// restart-dependent stall W11910 removed. So it is re-offered — while
		// still publishing `failed` and still owing the one incident.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		let prompts = 0;
		const { signal, runWait } = script([
			envelope([action]),
			() => { time.advance(config.retryMs * 4); return envelope([action]); },
		]);
		const settlement = settlementFor(config,
			{ spy, reads: [slot([surviving])], now: time.now });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true,
				sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() {
					prompts += 1;
					throw new Error("the turn died mid-attempt");
				},
				async stop() {},
			}) });
		assert.equal(prompts, 2,
			"the unspent recovery wake was not re-delivered");
		assert.ok(!spy.published.some(([state]) => state === "idle"),
			JSON.stringify(spy.published));
		// AND ONE INCIDENT ACROSS BOTH TURNS. W55705 review [P1]: the retry
		// path used to clear the fence before the read, so the second turn
		// filed the same failure again.
		assert.equal(spy.incidents.length, 1,
			`one stranded claim filed ${spy.incidents.length} incidents`);
	});

test("W55705: a secondary claim strands the lane and retains the offer",
	async () => {
		// The delivered assignment is gone and something ELSE occupies the
		// participant's one slot. That offer cannot be claimed, so spending a
		// turn on it would prove only that — it is retained, not presented.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const other = workAction("7ba67cb8-W999",
			{ episode: 77, claimed: true });
		const { signal, runWait } = script([
			envelope([action]),
			() => { time.advance(config.retryMs * 4); return envelope([action]); },
		]);
		const settlement = settlementFor(config,
			{ spy, reads: [slot([other])], now: time.now });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		assert.equal(
			events(log).filter((e) => e.event === "prompt/start").length, 1,
			"a turn was spent against a slot that could not be claimed");
		assert.ok(!spy.published.some(([state]) => state === "idle"));
		assert.equal(spy.incidents.length, 1);
		assert.equal(spy.incidents[0].work, "7ba67cb8-W999",
			"the incident named the offer rather than the occupant");
	});

test("W55705: a newly stranded slot stops the rest of the same envelope",
	async () => {
		// W55705 review (2026-09-01T03:41:20Z) [P1]. The outer fence check
		// runs ONCE per envelope, so a `continue` after a stranded settlement
		// let the next fresh action revalidate against its own successful read
		// and start a turn — after the bridge had just failed to prove the
		// claim slot safe. Fail-open for exactly the unreadable case.
		//
		// A POKE is the second action on purpose: it delivers beside Work
		// rather than waiting behind the claim slot, so if the loop kept
		// going it really would reach the agent.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163", { episode: 5 }),
			          pokeAction(9)]),
		]);
		const settlement = settlementFor(config, {
			spy, now: time.now,
			// The settlement read fails; the poke's own pre-turn revalidation
			// would have succeeded.
			reads: [new Error("the authority did not answer")] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		const prompts = events(log).filter((e) => e.event === "prompt/start");
		assert.equal(prompts.length, 1,
			"a turn started after the claim slot could not be proved safe");
		assert.ok(!spy.published.some(([state]) => state === "idle"));
	});

test("W55705: a stranded lane retains readiness until a canonical release",
	async () => {
		// The whole recovery arc: strand, retain, and resume the moment a
		// canonical read says the slot is free — without anybody restarting
		// this process, which is the operator-facing point of the fence.
		const { log, config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const other = workAction("7ba67cb8-W999",
			{ episode: 77, claimed: true });
		const later = () => { time.advance(RECONCILE_MS + 1);
			return envelope([action]); };
		const { signal, runWait } = script([
			envelope([action]), later, later,
		]);
		const settlement = settlementFor(config, {
			spy, now: time.now,
			reads: [slot([other]), slot([other]), slot([]), slot([])] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		assert.equal(
			events(log).filter((e) => e.event === "prompt/start").length, 2,
			"the retained offer never resumed after the release");
		assert.ok(spy.published.some(([state]) => state === "idle"),
			"delivery resumed without ever advertising capacity again");
	});

// -- the state machine, in isolation -----------------------------------------

test("W55705: a recoverable retry keeps its fence identity and files once",
	async () => {
		// W55705 review [P1]. The old retry saved only the boolean, set
		// `this.fence = null`, and re-minted around a fresh read — so the
		// acknowledgement, the `since` instant and the recorded authority all
		// belonged to a fence that no longer existed.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [slot([surviving])] });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		assert.equal(await f.settle.settle(action), "recoverable");
		const { since, authority } = f.settle.fence;
		assert.equal(f.settle.fence.incidentFiled, true);
		f.time.advance(5000);
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(f.spy.incidents.length, 1);
		assert.equal(f.settle.fence.since, since,
			"the same stranded fact was re-minted around a new instant");
		assert.equal(f.settle.fence.authority, authority);
		assert.equal(f.settle.fenced(), false,
			"an exact claimed Work is recoverable, not stranded");
	});

test("W55705: a recoverable retry against another authority stays fenced",
	async () => {
		// The record's own fail-closed boundary: a different authority
		// answering for this participant is not evidence that the old claim
		// was released. The old code could not even see the difference,
		// because it compared against a fence it had just cleared.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [
			slot([surviving]),
			slot([surviving], { uuid: OTHER_UUID })] });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(await f.settle.settle(action), "stranded");
		assert.equal(f.settle.fenced(), true);
		assert.equal(f.settle.fence.authority, UUID,
			"the foreign authority was adopted into the fence");
		assert.equal(f.settle.fence.drift, OTHER_UUID);
		assert.equal(f.spy.incidents.length, 1);
	});

test("W55705: a canonical read that names no authority is drift, not a match",
	async () => {
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const anonymous = slot([surviving]);
		delete anonymous.authority_uuid;
		const f = focused({ reads: [slot([surviving]), anonymous] });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(await f.settle.settle(action), "stranded");
		assert.equal(f.settle.fence.authority, UUID);
	});

test("W55705: an unreadable answer keeps the fence rather than minting a second",
	async () => {
		// "I could not ask" is not a new fact about the slot. Minting an
		// `unreadable` fence here would give one stranded claim a second
		// identity, a second incident, and no recorded authority.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [
			slot([surviving]), new Error("the authority did not answer")] });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(await f.settle.settle(action), "stranded");
		assert.equal(f.settle.fence.work, "7ba67cb8-W163");
		assert.equal(f.settle.fence.correlation, "claimed");
		assert.equal(f.settle.fence.authority, UUID);
		assert.equal(f.spy.incidents.length, 1);
	});

test("W55705: a successor claim mints its own unfiled incident", async () => {
	// W55705 review [P1]: a fence for W1/episode 11 followed by a canonical
	// W2/episode 22 stayed filed against W1 and emitted nothing for W2 — so
	// the second stranded claim had no operator notice at all.
	const first = workAction("7ba67cb8-W163", { episode: 11, claimed: true });
	const second = workAction("7ba67cb8-W999", { episode: 22, claimed: true });
	const f = focused({ reads: [slot([first]), slot([second])] });
	assert.equal(await f.settle.settle(
		workAction("7ba67cb8-W163", { episode: 11 })), "recoverable");
	assert.equal(f.spy.incidents.length, 1);
	f.time.advance(RECONCILE_MS + 1);
	await f.settle.reconcile();
	assert.equal(f.settle.fence.work, "7ba67cb8-W999");
	assert.equal(f.settle.fence.episode, 22);
	assert.equal(f.spy.incidents.length, 2,
		"the successor inherited its predecessor's acknowledgement");
	assert.equal(f.spy.incidents[1].work, "7ba67cb8-W999");
	assert.equal(f.settle.fence.incidentFiled, true);
});

test("W55705: the same Work under a newer episode is a successor, not a release",
	async () => {
		// A newer assignment episode of the SAME Work occupies the one slot.
		// It is not the delivered episode and it is not nothing.
		const old = workAction("7ba67cb8-W163", { episode: 11, claimed: true });
		const fresher = workAction("7ba67cb8-W163",
			{ episode: 99, claimed: true });
		const f = focused({ reads: [slot([old]), slot([fresher])] });
		await f.settle.settle(workAction("7ba67cb8-W163", { episode: 11 }));
		f.time.advance(RECONCILE_MS + 1);
		await f.settle.reconcile();
		assert.equal(f.settle.settled(), true, "a newer episode read as release");
		assert.equal(f.settle.fence.episode, 99);
		assert.equal(f.settle.fence.correlation, "secondary");
		assert.equal(f.spy.incidents.length, 2);
	});

test("W55705: a late acknowledgement is never transferred to a successor",
	async () => {
		// W55705 review [P1]: the old ordering copied a `true` acknowledgement
		// onto whatever fence happened to be current when the publication
		// landed, suppressing the retry for the wrong Work and episode.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		let settle;
		const f = focused({
			reads: [slot([surviving])],
			incident: async (_row, n) => {
				if (n === 1) {
					// The fence is superseded WHILE this publication is in
					// flight.
					settle.fence = { ...settle.fence, work: "7ba67cb8-W999",
						episode: 77, incidentFiled: false };
				}
				return true;
			} });
		settle = f.settle;
		await f.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
		assert.equal(f.settle.fence.work, "7ba67cb8-W999");
		assert.equal(f.settle.fence.incidentFiled, false,
			"the successor was marked filed by its predecessor's answer");
	});

test("W55705: the incident is retried when publication refuses or throws",
	async () => {
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({
			reads: [slot([surviving])],
			incident: async (_row, n) => {
				if (n === 1) return false;
				if (n === 2) throw new Error("the publication transport died");
				return true;
			} });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		await f.settle.settle(action);
		assert.equal(f.settle.fence.incidentFiled, false,
			"a refused publication was recorded as filed");
		f.time.advance(RECONCILE_MS + 1);
		await f.settle.reconcile();
		assert.equal(f.settle.fence.incidentFiled, false,
			"a thrown publication was recorded as filed");
		f.time.advance(RECONCILE_MS + 1);
		await f.settle.reconcile();
		assert.equal(f.settle.fence.incidentFiled, true);
		assert.equal(f.spy.incidents.length, 3);
	});

test("W55705: two concurrent observations file one incident", async () => {
	// `settle` and `reconcile` can both reach the publication, and two in
	// flight for one fence is two incidents for one stranded claim.
	const surviving = workAction("7ba67cb8-W163", { episode: 5, claimed: true });
	let release;
	const gate = new Promise((resolve) => { release = resolve; });
	const f = focused({
		reads: [slot([surviving])],
		incident: async () => { await gate; return true; } });
	const action = workAction("7ba67cb8-W163", { episode: 5 });
	const first = f.settle.settle(action);
	// A second observation arrives while the first publication is in flight.
	await new Promise((resolve) => setImmediate(resolve));
	const second = f.settle.fileIncident();
	release();
	await Promise.all([first, second]);
	assert.equal(f.spy.incidents.length, 1,
		`one stranded claim filed ${f.spy.incidents.length} incidents`);
});

// -- persistence, and the difference between a fence and a durable one --------

test("W55705: an uncommitted marker strands the lane rather than looking durable",
	async () => {
		// W55705 review [P1]. `store.save` returns a boolean SO a caller can
		// tell an in-process fence from a restart-durable one, and the old
		// code assigned that boolean and then ignored it. An unwritable state
		// directory therefore produced a bridge that looked fenced while a
		// restart would have found nothing and delivered into the same
		// occupied slot.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [slot([surviving])],
			store: scriptedStore({ onSave: () => false }) });
		const verdict = await f.settle.settle(
			workAction("7ba67cb8-W163", { episode: 5 }));
		assert.equal(verdict, "stranded",
			"an uncommitted fence was reported as an ordinary recoverable one");
		assert.equal(f.settle.fenced(), true);
		assert.equal(f.settle.fence.correlation, "claimed");
		assert.equal(f.settle.fence.durable, false);
	});

test("W55705: an uncommitted acknowledgement is not reported durable",
	async () => {
		// The marker commits and the acknowledgement update does not. A
		// restart would then file the same incident again, so the lane stays
		// fenced rather than reporting a durability it does not have.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [slot([surviving])],
			store: scriptedStore({ onSave: (_record, n) => n === 1 }) });
		await f.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
		assert.equal(f.settle.fence.incidentFiled, true,
			"this process must not publish the same incident twice");
		assert.equal(f.settle.fence.durable, false);
		assert.equal(f.settle.fenced(), true,
			"a fence whose acknowledgement is not on disk kept delivering");
	});

test("W55705: a clear nobody could confirm keeps the fence", async () => {
	const other = workAction("7ba67cb8-W999", { episode: 77, claimed: true });
	const f = focused({ reads: [slot([other]), slot([])],
		store: scriptedStore({ onClear: () => false }) });
	await f.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
	assert.equal(f.settle.fenced(), true);
	f.time.advance(RECONCILE_MS + 1);
	assert.equal(await f.settle.reconcile(), "fenced");
	assert.equal(f.settle.settled(), true,
		"a delete nobody could confirm became an in-memory clear");
});

// -- restart ------------------------------------------------------------------

test("W55705: a restored recoverable marker is fenced until the authority matches",
	async () => {
		// W55705 review [P1]. `restore()` believes the file — correctly — but
		// `fenced()` answered false for a `claimed` marker, so a dispatcher
		// restarted against ANOTHER authority skipped reconciliation entirely
		// and delivered on the strength of a fence taken somewhere else.
		const { config } = rig();
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const first = focused({ config, reads: [slot([surviving])] });
		await first.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
		assert.equal(first.settle.fenced(), false);

		// A NEW PROCESS over the same state directory.
		const restarted = focused({ config, reads: [slot([surviving])] });
		assert.equal(restarted.settle.restore().state, "present");
		assert.equal(restarted.settle.fenced(), true,
			"a restored marker was deliverable before any canonical read");
		restarted.time.advance(RECONCILE_MS + 1);
		await restarted.settle.reconcile();
		assert.equal(restarted.settle.fenced(), false,
			"a matching authority did not re-admit the recovery delivery");
		assert.equal(restarted.settle.fence.correlation, "claimed");

		// AND THE DRIFTED RESTART, which must not.
		const drifted = focused({ config,
			reads: [slot([surviving], { uuid: OTHER_UUID })] });
		assert.equal(drifted.settle.restore().state, "present");
		drifted.time.advance(RECONCILE_MS + 1);
		await drifted.settle.reconcile();
		assert.equal(drifted.settle.fenced(), true,
			"a restart pointed at another authority delivered anyway");
		assert.equal(drifted.settle.fence.authority, UUID);
	});

test("W55705: a restarted bridge delivers nothing before the marker is checked",
	async () => {
		// The same rule where it matters: through `runBridge`, with the
		// marker on disk and the configured authority changed under it.
		const { log, config } = rig();
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const seeded = focused({ config, reads: [slot([surviving])] });
		await seeded.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));

		const spy = runtimeSpy();
		const time = clock();
		const settlement = settlementFor(config, { spy, now: time.now,
			reads: [slot([surviving], { uuid: OTHER_UUID })] });
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163", { episode: 5 })]),
		]);
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement });
		assert.equal(
			events(log).filter((e) => e.event === "prompt/start").length, 0,
			"a restart delivered before comparing the marker's authority");
		assert.ok(!spy.published.some(([state]) => state === "idle"),
			JSON.stringify(spy.published));
	});

test("W55705: a damaged marker stays fenced and its bytes are preserved",
	async () => {
		const { config } = rig();
		mkdirSync(config.stateDir, { recursive: true });
		const marker = join(config.stateDir,
			`${CLAIM_SLOT_KEY(config.baton.participant)}.acp-settlement.json`);
		writeFileSync(marker, "{ this is not a settlement record");
		const f = focused({ config, reads: [slot([])] });
		assert.equal(f.settle.restore().state, "damaged");
		assert.equal(f.settle.fenced(), true,
			"a damaged marker was read as an absent one");
		assert.equal(f.settle.fence.correlation, "unreadable");
		assert.equal(readFileSync(`${marker}.damaged`, "utf8"),
			"{ this is not a settlement record",
			"the corrupt bytes were not preserved for inspection");
	});

test("W55705: an exact canonical release clears a restored marker", async () => {
	const { config } = rig();
	const other = workAction("7ba67cb8-W999", { episode: 77, claimed: true });
	const first = focused({ config, reads: [slot([other])] });
	await first.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
	const restarted = focused({ config, reads: [slot([])] });
	assert.equal(restarted.settle.restore().state, "present");
	restarted.time.advance(RECONCILE_MS + 1);
	assert.equal(await restarted.settle.reconcile(), "clear");
	assert.equal(restarted.settle.settled(), false);
	// AND THE MARKER IS GONE, so a third process starts clean.
	const third = focused({ config, reads: [slot([])] });
	assert.equal(third.settle.restore().state, "absent");
});

// -- the boundaries this Work does NOT cross ---------------------------------

test("W55705: a delegated runtime locator is named only when supplied",
	async () => {
		// The ACP process domain does not contain a container the Docker
		// daemon created — run7 is the direct evidence — and the bridge has no
		// trusted structured source for its id. So it says the absence is
		// UNPROVED rather than inventing a locator or implying cleanliness.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const silent = focused({ reads: [slot([surviving])] });
		await silent.settle.settle(action);
		assert.match(silent.spy.incidents[0].detail,
			/any delegated runtime is not proved absent/);

		const told = focused({ reads: [slot([surviving])] });
		await told.settle.settle(action,
			{ runtimeLocator: "container:afed4c76aebe" });
		assert.match(told.spy.incidents[0].detail,
			/delegated runtime was reported at container:afed4c76aebe/);
	});

test("W55705: settlement kills nothing, releases nothing and accepts nothing",
	async () => {
		// A property of the SOURCE, because it is the kind of thing a later
		// edit adds helpfully. The module owns a fence and a notice; every
		// remedy it knows is prose for an operator.
		const source = readFileSync(
			join(HERE, "..", "src", "acp_settlement.mjs"), "utf8");
		for (const forbidden of ["child_process", "execFile", "spawn",
		                         "docker", "process.kill"]) {
			assert.ok(!source.includes(forbidden),
				`the settlement reaches for ${forbidden}`);
		}
		// The remedy it publishes is an operator's `release`, and it says the
		// runtime must be proved absent FIRST.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const f = focused({ reads: [slot([surviving])] });
		await f.settle.settle(workAction("7ba67cb8-W163", { episode: 5 }));
		assert.match(f.settle.fence.remedy,
			/release work=7ba67cb8-W163 expect=baton\.claude episode=5/);
		assert.match(f.settle.fence.remedy, /Prove any delegated runtime absent/);
	});

test("W55705: a process-domain teardown failure is the stronger fence",
	async () => {
		// The two fences are independent and neither clears the other. A
		// teardown that cannot be proved is FATAL and comes first, so no
		// canonical settlement runs behind it and nothing publishes `idle`
		// beside a domain that may still be alive.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const settlement = settlementFor(config,
			{ spy, now: time.now, reads: [slot([])] });
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163", { episode: 5 })]),
		]);
		await assert.rejects(runBridge(config, {
			signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true,
				sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() {},
				async stop() {
					throw new DomainTeardownError("the domain would not die");
				},
			}) }), DomainTeardownError);
		assert.ok(!spy.published.some(([state]) => state === "idle"));
		assert.equal(spy.incidents.length, 0,
			"a claim settlement ran behind an unprovable process domain");
		assert.equal(settlement.settled(), false,
			"the settlement fence was minted from a turn it never settled");
	});

// -- the incident needs an owner (approver ruling M58455) --------------------

test("W55705: a managed bridge refuses to start without a configured owner",
	async () => {
		// The deployment that produced this Work's incident ran with
		// `action_owner: null`, so the settlement would have fenced correctly
		// and then retried a notice that could never be filed. An ownerless
		// bridge is outside this contract rather than a degraded mode of it,
		// and the refusal lands BEFORE the lease and before the first wait.
		for (const runtime of [null, { provider: "claude" }]) {
			const { config } = rig();
			if (runtime === null) delete config.runtime;
			else config.runtime = runtime;
			const spy = runtimeSpy();
			const { signal, runWait } = script([envelope([])]);
			await assert.rejects(
				runBridge(config, { signal, runWait, logger: quiet,
					runtime: spy.runtime }),
				/runtime\.actionOwner is required/);
			assert.deepEqual(spy.published, [],
				"the runtime lease was published before the refusal");
		}
	});

test("W55705: a configured owner starts ordinarily", async () => {
	const { config } = rig();
	assert.equal(config.runtime.actionOwner, ACTION_OWNER);
	const spy = runtimeSpy();
	const { signal, runWait } = script([envelope([])]);
	await runBridge(config, { signal, runWait, logger: quiet,
		runtime: spy.runtime });
	assert.equal(spy.published[0][0], "start");
});

test("W55705: a stranded FAILED turn stops the rest of the envelope too",
	async () => {
		// The same break on the other path, and it needs its own case: the
		// failure branch has its own settlement call and its own verdict
		// handling, so covering only the returned-prompt branch left half the
		// correction unproved. Measured — this case fails against a `continue`
		// here and passes against the `break`.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		let prompts = 0;
		const { signal, runWait } = script([
			envelope([workAction("7ba67cb8-W163", { episode: 5 }),
			          pokeAction(9)]),
		]);
		const settlement = settlementFor(config, { spy, now: time.now,
			reads: [new Error("the authority did not answer")] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true,
				sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() {
					prompts += 1;
					throw new Error("the turn died mid-attempt");
				},
				async stop() {},
			}) });
		assert.equal(prompts, 1,
			"a turn started after a failed turn stranded the claim slot");
		assert.ok(!spy.published.some(([state]) => state === "idle"));
	});

test("W55705: a settled release retires the marker a restart would find",
	async () => {
		// The in-memory clear and the durable one are different acts, and the
		// second is the one a RESTART sees. A fence cleared only in memory
		// leaves a marker that resurrects on the next start and fences a lane
		// whose claim is long gone.
		const { config } = rig();
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const f = focused({ config, reads: [slot([surviving]), slot([])] });
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(focused({ config, reads: [slot([])] })
			.settle.restore().state, "present",
		"the fence was never durable in the first place");
		assert.equal(await f.settle.settle(action), "released");
		assert.equal(f.settle.settled(), false);
		assert.equal(focused({ config, reads: [slot([])] })
			.settle.restore().state, "absent",
		"a restart would have found a marker for a released claim");
	});

test("W55705: a release whose delete failed stays fenced on the settle path",
	async () => {
		// The companion to the reconcile case above, and it needed its own:
		// deleting the guard around `store.clear` still deletes the marker in
		// the ordinary case, so only a FAILING delete can prove the fence
		// survives one. A marker nobody could remove outlives this process,
		// and a lane that resumed on the strength of it would be fenced again
		// by its own restart.
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const f = focused({ reads: [slot([surviving]), slot([])],
			store: scriptedStore({ onClear: () => false }) });
		assert.equal(await f.settle.settle(action), "recoverable");
		assert.equal(await f.settle.settle(action), "stranded",
			"a canonically released claim resumed over an undeleted marker");
		assert.equal(f.settle.settled(), true);
		assert.equal(f.settle.fenced(), true);
	});

test("W55705: a drifted authority is fenced BEFORE a turn, not after one",
	async () => {
		// W55705 return review (2026-09-01T04:30:00Z) [P1]. A durable,
		// verified `claimed` fence is deliberately not `fenced()` -- that is
		// W11910's recoverable redelivery -- so the loop skipped
		// reconciliation, revalidated and prompted, and only the POST-turn
		// settlement compared the answer with the fence's recorded authority.
		// One action from the new authority had already reached the model.
		//
		// ONE BRIDGE, A THEN B, and the assertion is a count: the A prompt is
		// spent and the B prompt is not.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const seen = [];
		const { signal, runWait } = script([
			envelope([action]),
			() => {
				time.advance(config.retryMs * 8);
				// THE SAME ACTION, FROM ANOTHER AUTHORITY.
				return envelope([action], { uuid: OTHER_UUID });
			},
		]);
		const settlement = settlementFor(config, {
			spy, now: time.now, reads: [slot([surviving])] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true,
				sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() {
					// FAILED, so the offer is an unspent wake and is really
					// re-delivered by the ordinary rules -- which is what
					// makes the second poll reach the gate under test.
					seen.push(true);
					throw new Error("the turn died mid-attempt");
				},
				async stop() {},
			}) });
		assert.equal(seen.length, 1,
			"an action from another authority reached the model");
		// AND THE FENCE KEPT THE AUTHORITY IT WAS TAKEN AGAINST.
		assert.equal(settlement.fence.authority, UUID);
		assert.equal(settlement.fence.drift, OTHER_UUID);
		assert.equal(settlement.fenced(), true);
		assert.ok(!spy.published.some(([state]) => state === "idle"));
	});

test("W55705: an unnamed authority is drift rather than a match, before a turn",
	async () => {
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W163", { episode: 5 });
		const surviving = workAction("7ba67cb8-W163",
			{ episode: 5, claimed: true });
		const settlement = settlementFor(config, {
			spy, now: time.now, reads: [slot([surviving])] });
		await settlement.settle(action);
		assert.equal(settlement.fenced(), false, "the premise is a live offer");
		for (const unnamed of [undefined, null, 7]) {
			assert.equal(await settlement.admits(unnamed), false,
				`${unnamed} was read as a match`);
		}
		assert.equal(settlement.fence.authority, UUID);
	});

test("W55705: a bridge may not owe its own stranded-claim incident",
	async () => {
		// W55705 return review [P1]. Naming the runner explicitly reaches the
		// same deadlock as inferring it: while a stranded settlement retains
		// every readiness action, the incident obligation addressed back to
		// this participant is one of them -- queued behind the fence it is
		// supposed to resolve.
		//
		// AND IT REFUSES BEFORE ROLE LOADING, the lease and the first wait,
		// which the injected instruction loader and the empty publication
		// both assert.
		const { config } = rig();
		config.runtime.actionOwner = "baton.claude";
		assert.equal(config.runtime.actionOwner, config.baton.participant);
		const spy = runtimeSpy();
		let waited = 0;
		await assert.rejects(
			productionRunBridge(config, {
				signal: new AbortController().signal,
				runWait: async () => { waited += 1; return envelope([]); },
				logger: quiet, runtime: spy.runtime,
				loadInstructions: async () => {
					assert.fail("the role was resolved before the refusal");
				} }),
			/is this bridge's own participant/);
		assert.equal(waited, 0, "a wait was armed before the refusal");
		assert.deepEqual(spy.published, [],
			"the runtime lease was published before the refusal");
	});

test("W55705: a same-authority SUCCESSOR is reconciled before a turn is spent",
	async () => {
		// W55705 return review (2026-09-01T05:03:30Z) [P1]. `admits` answers
		// whose ledger is talking; once it agreed, a verified `claimed` fence
		// made `fenced()` false and every fresh action went on to prompt. So
		// W1's fence was still current when W2 was delivered, and only the
		// POST-turn settlement replaced it and filed W2's incident -- after
		// a turn had been spent against a slot W2 could not claim.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const first = workAction("7ba67cb8-W1", { episode: 11 });
		const firstHeld = workAction("7ba67cb8-W1",
			{ episode: 11, claimed: true });
		const second = workAction("7ba67cb8-W2", { episode: 22 });
		const secondHeld = workAction("7ba67cb8-W2",
			{ episode: 22, claimed: true });
		let prompts = 0;
		const { signal, runWait } = script([
			envelope([first]),
			() => { time.advance(config.retryMs * 8); return envelope([second]); },
		]);
		const settlement = settlementFor(config, {
			spy, now: time.now,
			// SAME AUTHORITY throughout: this case is about identity, not
			// about drift.
			reads: [slot([firstHeld]), slot([secondHeld])] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true, sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText() { prompts += 1; },
				async stop() {},
			}) });
		assert.equal(prompts, 1,
			"a successor claim was spent before the fence was reconciled");
		// AND THE SUCCESSOR IS RECORDED, through reconciliation rather than
		// through a turn: its own fence, its own unfiled incident.
		assert.equal(settlement.fence.work, "7ba67cb8-W2");
		assert.equal(settlement.fence.episode, 22);
		assert.equal(spy.incidents.length, 2, JSON.stringify(spy.incidents));
		assert.equal(spy.incidents[0].work, "7ba67cb8-W1");
		assert.equal(spy.incidents[1].work, "7ba67cb8-W2");
		assert.ok(!spy.published.some(([state]) => state === "idle"));
	});

test("W55705: a later wake beside the exact recovery wake is retained",
	async () => {
		// The second probe. The FAILED recovery wake correctly stays eligible
		// -- W11910's exception is exactly one action wide -- while the poke
		// beside it does not, because settling it turned the same W1 fence
		// from `claimed` to `held` and filed a SECOND incident for one
		// stranded claim.
		const { config } = rig();
		const spy = runtimeSpy();
		const time = clock();
		const action = workAction("7ba67cb8-W1", { episode: 11 });
		const held = workAction("7ba67cb8-W1", { episode: 11, claimed: true });
		const seen = [];
		const { signal, runWait } = script([
			envelope([action, pokeAction(9)]),
		]);
		const settlement = settlementFor(config, {
			spy, now: time.now, reads: [slot([held])] });
		await runBridge(config, { signal, runWait, logger: quiet, now: time.now,
			runtime: spy.runtime, settlement,
			sessionFactory: () => ({
				alive: () => true, sessionId: "sess-1",
				async start() { return "sess-1"; },
				async promptText(text) {
					seen.push(text);
					throw new Error("the turn died mid-attempt");
				},
				async stop() {},
			}) });
		assert.equal(seen.length, 1,
			"a later wake was spent while the exact claim was unreconciled");
		assert.match(seen[0], /W1/);
		// ONE STRANDED CLAIM, ONE INCIDENT, and the fence is still the
		// delivered assignment's rather than a weaker reading of it.
		assert.equal(spy.incidents.length, 1, JSON.stringify(spy.incidents));
		assert.equal(settlement.fence.correlation, "claimed");
		assert.equal(settlement.fence.work, "7ba67cb8-W1");
		assert.equal(settlement.fence.episode, 11);
	});

test("W55705: the exact wake is the whole identity, not just the Work",
	async () => {
		// A NEWER EPISODE OF THE SAME WORK IS NOT THE WAKE THAT WAS SPENT.
		// W11910's exception names the same participant AND assignment
		// episode, so matching on the Work alone would re-admit a different
		// assignment behind a fence taken for the old one.
		const surviving = workAction("7ba67cb8-W1",
			{ episode: 11, claimed: true });
		const f = focused({ reads: [slot([surviving]), slot([surviving])] });
		const wake = workAction("7ba67cb8-W1", { episode: 11 });
		assert.equal(await f.settle.settle(wake), "recoverable");
		assert.equal(await f.settle.permits(wake), true,
			"the exact unspent recovery wake was retained");
		for (const other of [workAction("7ba67cb8-W1", { episode: 99 }),
		                     workAction("7ba67cb8-W1",
		                                { episode: 11, generation: 7 })]) {
			assert.equal(await f.settle.permits(other), false,
				`${other.action_key} was read as the exact wake`);
		}
	});

test("W55705: a STRANDED fence retains even its own offer's action",
	async () => {
		// The recoverable exception belongs to a fence that is not fenced. A
		// `secondary` fence still records the offer it was taken for, so
		// matching the offer without first asking whether the lane is fenced
		// would hand the one blocked case its own action back.
		const other = workAction("7ba67cb8-W999", { episode: 77, claimed: true });
		const f = focused({ reads: [slot([other])] });
		const wake = workAction("7ba67cb8-W1", { episode: 11 });
		assert.equal(await f.settle.settle(wake), "stranded");
		assert.equal(f.settle.fenced(), true);
		assert.equal(f.settle.fence.offered.work, "7ba67cb8-W1");
		assert.equal(await f.settle.permits(wake), false,
			"a stranded lane admitted the action its fence was taken for");
	});
