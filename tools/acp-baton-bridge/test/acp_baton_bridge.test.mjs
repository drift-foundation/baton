// W163 slice A acceptance: the generic ACP readiness client against a
// REAL fake-agent subprocess speaking the pinned SDK over stdio.

import test from "node:test";
import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync,
         writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { validateConfig } from "../src/config.mjs";
import { runBridge as productionRunBridge } from "../src/acp_baton_bridge.mjs";
import { AcpAgentSession } from "../src/acp_agent_session.mjs";
import { episodeStillLive, validateEnvelope } from "../src/baton_readiness.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FAKE_AGENT = join(HERE, "fake_acp_agent.mjs");
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

// W49: a Work action carries its assignment EPISODE and the accepted
// configuration generation, and the key must agree with both.
function workAction(id, { title = "t", episode = 1, generation = 1 } = {}) {
	return { kind: "work",
	         action_key: `work:${id}:${episode}:g${generation}`,
	         work: id, episode_seq: episode, config_generation: generation,
	         local_id: id.split("-").pop(), title, phase: "queued",
	         claimed: false };
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
function rig({ env = {}, participant = "baton.claude",
               role = "impl", sessionMode = "new", policyResources } = {}) {
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
			return steps[calls++];
		},
	};
}

const quiet = { info() {}, warn() {} };

const runBridge = (config, options = {}) => productionRunBridge(config, {
	loadInstructions: async () => ({
		participant: config.baton.participant,
		role: config.baton.role ?? "impl",
		instructions: "Honor the configured participant role.",
		configurationGeneration: 1,
	}),
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
	assert.match(prompt.text, /Apply standing v11 Baton policy\.$/);
	assert.equal(prompt.mode, "bypassPermissions",
		"the turn ran outside the configured mode");
	assert.doesNotMatch(prompt.text, /body|EXTERNAL EVENT/);
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
	const { log, config } = rig({ env: { FAKE_ACP_SLOW_MS: "120" } });
	const { signal, runWait } = script([
		envelope([workAction("7ba67cb8-W163"),
		          workAction("7ba67cb8-W164"),
		          workAction("7ba67cb8-W165")]),
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
			session: config.session, permissionMode: config.permissionMode,
			policyResources: config.policyResources,
			stateDir: config.stateDir, retryMs: config.retryMs,
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
		session: config.session, permissionMode: config.permissionMode,
		policyResources: [locked],
		stateDir: config.stateDir, retryMs: config.retryMs,
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
	assert.equal(live, true);
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
	assert.equal(stale, false,
		"a different episode of the same Work was accepted as still live");
});

test("a queued prompt whose episode ended is dropped before the agent turn", async () => {
	const { log, config } = rig();
	const action = workAction("7ba67cb8-W27");
	const { signal, runWait } = script([envelope([action])]);
	const infos = [];
	// the Work was claimed/passed/closed while this prompt sat queued:
	// the revalidation read no longer carries the exact episode key
	await runBridge(config, { signal, runWait,
		revalidate: async () => false,
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
		revalidate: async (action) => action.episode_seq === 9 || live,
		logger: quiet });
	const prompts = events(log).filter((entry) => entry.event === "prompt/start");
	assert.equal(prompts.length, 1,
		"the dead episode was retried, or the new one was suppressed");
	assert.match(prompts[0].text, /W27/);
});

test("revalidation passing leaves ordinary delivery untouched", async () => {
	const { log, config } = rig();
	const set = [workAction("7ba67cb8-W163")];
	const { signal, runWait } = script([envelope(set), envelope(set)]);
	await runBridge(config, { signal, runWait,
		revalidate: async () => true, logger: quiet });
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
		assert.match(prompts[0].text, /^\[BATON READY\].*Apply standing v11 Baton policy\.$/);
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
			session: config.session, permissionMode: config.permissionMode,
			policyResources: config.policyResources,
			stateDir: config.stateDir, retryMs: config.retryMs,
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

function runtimeSpy() {
	const published = [];
	return {
		published,
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
		};
		const ok = validateConfig({ ...base, runtime: {
			provider: "Anthropic", model: "claude-opus-5",
			actionOwner: "baton.slaw" } });
		assert.deepEqual(ok.runtime, { provider: "Anthropic",
			model: "claude-opus-5", actionOwner: "baton.slaw" });
		// Absent is absent — nothing is inferred from the agent command
		// or from the participant's name.
		const bare = validateConfig(base);
		assert.deepEqual(bare.runtime, { provider: undefined,
			model: undefined, actionOwner: undefined });
		assert.throws(() => validateConfig({ ...base,
			runtime: { actionOwner: "slaw" } }), /team\.member/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { provider: "" } }), /non-empty/);
		assert.throws(() => validateConfig({ ...base,
			runtime: { guessed: "x" } }), /not a runtime metadata field/);
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
