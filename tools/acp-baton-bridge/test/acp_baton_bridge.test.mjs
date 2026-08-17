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
import { runBridge } from "../src/acp_baton_bridge.mjs";
import { AcpAgentSession } from "../src/acp_agent_session.mjs";
import { episodeStillLive } from "../src/baton_readiness.mjs";

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

function rig({ env = {}, participant = "baton.claude",
               sessionMode = "new", policyResources } = {}) {
	const home = mkdtempSync(join(tmpdir(), "acp-bridge-"));
	const log = join(home, "agent-log.jsonl");
	writeFileSync(log, "");
	const policy = policyResources ?? [join(home, "policy.json")];
	if (!policyResources) writeFileSync(policy[0], "{}\n");
	const config = validateConfig({
		baton: { binary: "/unused/baton", config: "/unused/baton.json",
		         participant },
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
