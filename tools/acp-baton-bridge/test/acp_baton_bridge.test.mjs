// W163 slice A acceptance: the generic ACP readiness client against a
// REAL fake-agent subprocess speaking the pinned SDK over stdio.

import test from "node:test";
import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { validateConfig } from "../src/config.mjs";
import { runBridge } from "../src/acp_baton_bridge.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FAKE_AGENT = join(HERE, "fake_acp_agent.mjs");
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

function workAction(id, { title = "t" } = {}) {
	return { kind: "work", action_key: `work:${id}`, work: id,
	         local_id: id.split("-").pop(), title, phase: "queued",
	         claimed: false };
}

function envelope(actions, { timedOut = false,
                             participant = "baton.claude",
                             uuid = UUID } = {}) {
	return {
		protocol_version: 11,
		projection_version: "6.0",
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
