// W93 slice 4: the adapter half of the participant runtime lease.
//
// `baton.tuner` held W22 while its Codex turn sat on a command-approval
// prompt. The dispatcher logged the exact `requestApproval` event and
// Baton showed `active` with a Handler, because that is all Baton had.
// Slice 3 gave the authority somewhere to put the runner's own state;
// this is the dispatcher and the ACP bridge finally filling it in.
//
// What these tests hold: only OBSERVED transitions are published,
// `offline`/`unknown` are never published because the authority derives
// them, no runtime report can break the wake path, and nothing here
// asks a provider or wakes a model to find anything out.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { codexBatonBridge } from "../src/codex_baton_bridge.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";
import {
	RuntimePublisher,
	classifyFailure,
	makeRuntimePublisher,
	silentPublisher,
} from "../src/runtime_publisher.mjs";

// W415: the dispatcher refuses to start unless the deployment-owned
// execpolicy file authorizes each managed participant's canonical Baton
// operations. These fixtures therefore need a real one.
import { mkdtempSync as _mkdtemp, writeFileSync as _write } from "node:fs";
import { join as _join } from "node:path";
import { rulesFor as _rulesFor } from "../src/exec_policy.mjs";
const _policyDir = _mkdtemp("/tmp/w415-fixture-policy-");
export const FIXTURE_POLICY = _join(_policyDir, "baton.rules");
_write(FIXTURE_POLICY, ["/srv/baton/baton.json", "/home/op/baton.json"]
	.flatMap((config) => ["baton.tuner", "baton.codex", "a.b"]
		.flatMap((participant) => _rulesFor({
			binary: "/opt/baton/bin/baton", config, participant })))
	.join("\n") + "\n");

const BATON = {
	binary: "/opt/baton/bin/baton",
	config: "/home/op/baton.json",
	participant: "baton.tuner",
};

function recorder() {
	const calls = [];
	return {
		calls,
		execute: async (file, args) => {
			calls.push({ file, args });
			return { stdout: "{}", stderr: "" };
		},
	};
}

function operands(call) {
	const out = {};
	for (const token of call.args) {
		const at = token.indexOf("=");
		if (at > 0) out[token.slice(0, at)] = token.slice(at + 1);
	}
	return out;
}

function verbs(calls) {
	return calls.map((call) => call.args[4]);
}

const quiet = { info() {}, warn() {}, error() {}, debug() {} };

// -- the publisher -----------------------------------------------------------

test("the lease names the launcher's three explicit facts", async () => {
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", incarnation: "run-1", execute: seen.execute });
	await publisher.start({ session: "thread-a" });
	const [call] = seen.calls;
	assert.equal(call.file, "/opt/baton/bin/baton");
	assert.deepEqual(call.args.slice(0, 5), [
		"--config", "/home/op/baton.json",
		"--participant", "baton.tuner", "runtime-start"]);
	const seenOperands = operands(call);
	assert.equal(seenOperands.incarnation, "run-1");
	assert.equal(seenOperands.adapter, "codex");
	assert.equal(seenOperands.session, "thread-a");
	// R5: every start carries a generic truthful replacement reason,
	// because the publisher performs no authority query and therefore
	// cannot know whether a previous incarnation exists.
	assert.ok(seenOperands.rationale);
});

test("the adapter family is stated, never inferred", async () => {
	const seen = recorder();
	// A participant named `baton.claude` driven by an ACP adapter is
	// the exact case a name-derived guess gets wrong.
	const publisher = new RuntimePublisher(
		{ ...BATON, participant: "baton.claude" },
		{ adapter: "acp", provider: "Anthropic", incarnation: "run-1",
		  execute: seen.execute });
	await publisher.start();
	assert.equal(operands(seen.calls[0]).adapter, "acp");
	assert.equal(operands(seen.calls[0]).provider, "Anthropic");
});

test("only observed states are publishable", async () => {
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	await publisher.start();
	for (const derived of ["offline", "unknown", "stuck", ""]) {
		await assert.rejects(() => publisher.state(derived),
			/not reported by an adapter|is not one of/);
	}
	for (const reported of ["idle", "working", "waiting-input",
	                        "retrying", "failed"]) {
		await publisher.state(reported, { cause: "approval" });
	}
	assert.deepEqual(verbs(seen.calls.slice(1)),
		Array(5).fill("runtime-state"));
});

test("a cause outside the closed set refuses before it reaches Baton",
	async () => {
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", execute: seen.execute });
		await publisher.start();
		await assert.rejects(
			() => publisher.state("failed", { cause: "because it broke" }),
			/not one of/);
		assert.equal(seen.calls.length, 1);
	});

test("a long detail is trimmed rather than refused", async () => {
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	await publisher.start();
	// A realistic long sentence rather than one opaque token, which the
	// secret scrubber would (correctly) replace outright.
	await publisher.state("failed", { cause: "internal",
		detail: "the adapter could not complete this turn ".repeat(40) });
	const detail = operands(seen.calls[1]).detail;
	assert.ok(detail.length <= 400, detail.length);
	assert.ok(detail.endsWith("…"), detail.slice(-20));
});

test("a failed report never propagates into the caller", async () => {
	const warnings = [];
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex",
		logger: { ...quiet, warn: (line) => warnings.push(line) },
		execute: async () => { throw new Error("baton is missing"); },
	});
	assert.equal(await publisher.start(), false);
	assert.match(warnings[0], /readiness is unaffected/);
});

test("a failed lease start remains retryable", async () => {
	let attempts = 0;
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex",
		logger: quiet,
		execute: async () => {
			attempts += 1;
			if (attempts === 1) throw new Error("authority not ready");
			return { stdout: "{}", stderr: "" };
		},
	});
	assert.equal(await publisher.start(), false);
	assert.equal(await publisher.start(), true,
		"one transient startup failure disabled this publisher forever");
	assert.equal(attempts, 2);
});

test("an ambiguous lease-start retry keeps one operation identity",
	async () => {
		const calls = [];
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			logger: quiet,
			execute: async (_file, args) => {
				calls.push({ args });
				// Model the dangerous shape: the CLI may have committed before
				// its process result was lost. The exact retry must therefore be
				// the SAME authority operation, not a second runtime-start.
				if (calls.length === 1) throw new Error("result lost after write");
				return { stdout: "{}", stderr: "" };
			},
		});
	assert.equal(await publisher.start(), false);
	assert.equal(await publisher.start(), true);
	const ids = calls.map((call) => operands(call)["op-id"]);
	assert.ok(ids[0], "runtime-start has no effectively-once identity");
	assert.equal(ids[1], ids[0],
		"the retry could not replay an ambiguously committed start");
});

test("an idle runner recovers from a transient lease-start failure",
	async () => {
		let attempts = 0;
		let scheduled;
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			logger: quiet,
			renewMs: 10,
			setTimer: (callback) => {
				scheduled = callback;
				return { unref() {} };
			},
			clearTimer() {},
			execute: async () => {
				attempts += 1;
				if (attempts === 1) throw new Error("authority starting");
				return { stdout: "{}", stderr: "" };
			},
		});
	assert.equal(await publisher.start(), false);
	assert.equal(typeof scheduled, "function",
		"an idle bridge has no later state event to repair its lease");
	scheduled();
	await new Promise((resolve) => setImmediate(resolve));
	assert.equal(attempts, 2);
});

test("scheduled lease-start recovery preserves every effective operand",
	async () => {
		const calls = [];
		let scheduled;
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			logger: quiet,
			renewMs: 10,
			setTimer: (callback) => {
				scheduled = callback;
				return { unref() {} };
			},
			clearTimer() {},
			execute: async (_file, args) => {
				calls.push(operands({ args }));
				if (calls.length === 1) throw new Error("result lost after write");
				return { stdout: "{}", stderr: "" };
			},
		});
		assert.equal(await publisher.start({
			session: "launch-session",
			rationale: "operator supplied restart reason",
		}), false);
		scheduled();
		await new Promise((resolve) => setImmediate(resolve));
		assert.deepEqual(calls[1], calls[0],
			"the same op-id retried with different effective operands");
	});

test("state-triggered lease-start recovery preserves launch operands",
	async () => {
		const calls = [];
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			logger: quiet,
			execute: async (_file, args) => {
				calls.push({ verb: args[4], operands: operands({ args }) });
				if (calls.length === 1) throw new Error("result lost after write");
				return { stdout: "{}", stderr: "" };
			},
		});
		assert.equal(await publisher.start({
			session: "launch-session",
			rationale: "operator supplied restart reason",
		}), false);
		await publisher.state("working", { session: "turn-session" });
		const starts = calls.filter((call) => call.verb === "runtime-start");
		assert.deepEqual(starts[1].operands, starts[0].operands,
			"state recovery changed the effectively-once start operation");
	});

test("publisher operations preserve observed order while start is pending",
	async () => {
		const calls = [];
		let releaseStart;
		const startGate = new Promise((resolve) => { releaseStart = resolve; });
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			execute: async (_file, args) => {
				calls.push(args[4]);
				if (args[4] === "runtime-start") await startGate;
				return { stdout: "{}", stderr: "" };
			},
		});
		const starting = publisher.start();
		const working = publisher.state("working");
		await new Promise((resolve) => setImmediate(resolve));
		assert.deepEqual(calls, ["runtime-start"],
			"runtime-state overtook the lease-opening write");
		releaseStart();
		await Promise.all([starting, working]);
		assert.deepEqual(calls, ["runtime-start", "runtime-state"]);
	});

test("a launcher always supplies a safe replacement rationale", async () => {
	// The authority requires rationale= whenever a previous incarnation
	// exists. The publisher deliberately does no authority query, so a
	// process restart has to carry a generic truthful reason on every start;
	// otherwise runtime publication works only for the first launch ever.
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	await publisher.start();
	assert.ok(operands(seen.calls[0]).rationale,
		"a restarted adapter cannot replace the previous runtime lease");
});

test("secret-looking failure text is never persisted as runtime detail",
	async () => {
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", execute: seen.execute });
		await publisher.start();
		await publisher.state("failed", { cause: "credential",
			detail: "Authorization: Bearer secret-token-123" });
		assert.doesNotMatch(operands(seen.calls[1]).detail,
			/secret-token-123/,
			"upstream errors can contain credentials and must be sanitized");
	});

test("state before start and anything after end are no-ops", async () => {
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	assert.equal(await publisher.state("working"), false);
	await publisher.start();
	await publisher.end({ cause: "internal" });
	assert.equal(await publisher.state("idle"), false);
	assert.equal(await publisher.end(), false);
	assert.deepEqual(verbs(seen.calls), ["runtime-start", "runtime-end"]);
});

test("an incomplete baton configuration publishes nothing at all",
	async () => {
		const publisher = makeRuntimePublisher({ binary: "/opt/baton" });
		assert.equal(publisher, silentPublisher);
		assert.equal(await publisher.start(), false);
		assert.equal(await publisher.state("working"), false);
	});

// -- the Codex dispatcher ----------------------------------------------------

class FakeClient extends EventEmitter {
	constructor() {
		super();
		this.connected = true;
		this.starts = [];
		// W3243: what the bridge answered a server-initiated request
		// with, and which turns it ended. Recorded because "it denied
		// and never approved" is the assertion this Work exists for.
		this.responses = [];
		this.interrupts = [];
		this.interruptFails = false;
	}

	respondError(id, code, message) {
		this.responses.push({ id, code, message });
		return true;
	}

	async interruptTurn(threadId, turnId) {
		this.interrupts.push({ threadId, turnId });
		if (this.interruptFails) throw new Error("interrupt refused");
		return { ok: true };
	}

	async connectAndInitialize() {
		this.connected = true;
		this.emit("connected", {});
	}

	async startTurn(threadId) {
		// Recorded, because "no model turn" is an assertion several
		// tests make and the only honest way to make it is to watch
		// the one call that starts one.
		this.starts.push(threadId);
		return { id: `turn-${threadId}`, status: "inProgress" };
	}

	async resume(threadId) {
		return { thread: { id: threadId, status: { type: "idle" },
			turns: [] } };
	}

	async readThread(threadId) {
		return { id: threadId, status: { type: "idle" }, turns: [] };
	}

	disconnect() {
		const wasConnected = this.connected;
		this.connected = false;
		if (wasConnected) this.emit("disconnected");
	}
}

function identifiedConfig(eventSocket =
		"/tmp/codex-event-bridge-runtime-unused.sock") {
	return validateConfig({
		servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
		targets: {
			tuner: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.tuner", role: "tuner", actionOwner: "ops.slaw" } },
		},
		roleInstructions: { binary: "/opt/baton/bin/baton", config: "/home/op/baton.json",
			execPolicyFile: FIXTURE_POLICY },
		eventSocket,
		quarantineDir: freshQuarantineDir(),
	});
}

// The configuration says identities and roleInstructions arrive
// together or not at all, so "no identity" is a whole deployment
// rather than one odd target.
function anonymousConfig() {
	return validateConfig({
		servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
		targets: { anon: { server: "local", threadId: "thread-b" } },
		eventSocket: "/tmp/codex-event-bridge-runtime-unused.sock",
		quarantineDir: freshQuarantineDir(),
	});
}

function dispatcherWithRuntime({ config = identifiedConfig(),
                                 runtimeFactory } = {}) {
	const published = [];
	const runtime = {
		incarnation: "run-1",
		async start(options) { published.push(["start", options]); },
		async state(state, options) { published.push([state, options]); },
		async incident(options) { published.push(["incident", options]); return true; },
		async facts(supplied, options) {
			published.push(["facts", { ...supplied, ...options }]);
			// The real publisher answers whether the publication
			// happened, and a caller that acts on that answer needs the
			// stub to keep the same contract.
			return true;
		},
		async end(options) { published.push(["end", options]); },
	};
	const fake = new FakeClient();
	const bridge = new EventBridge({
		config,
		logger: quiet,
		clientFactory: () => fake,
		runtimeFactory: runtimeFactory ?? ((_config, target) =>
			(target.identity ? runtime : silentPublisher)),
	});
	return { bridge, fake, published };
}

test("the approval request that started all this becomes waiting-input",
	async () => {
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("serverRequest", {
			id: 7,
			method: "item/commandExecution/requestApproval",
			params: { threadId: "thread-a" },
		});
		const entry = published.find(([state]) => state === "waiting-input");
		assert.ok(entry, JSON.stringify(published));
		assert.equal(entry[1].cause, "approval");
		assert.match(entry[1].detail, /requestApproval/);
		assert.equal(entry[1].session, "thread-a");
		await bridge.stop();
	});

test("the request is DENIED, never approved", async () => {
	// SUPERSEDED IN PART — W3243. This was "publishing the state is not
	// answering the request", and leaving it unanswered is precisely
	// what wedged the target: the turn waited for a human who was not
	// in that conversation while 24 readiness events queued behind it.
	//
	// The boundary that stands is the one that matters: the bridge
	// never APPROVES. It now answers with an explicit denial, which no
	// app-server can read as permission, and still forwards the
	// observation for anyone watching.
	const { bridge, fake } = dispatcherWithRuntime();
	const forwarded = [];
	bridge.on("serverRequest", (entry) => forwarded.push(entry));
	await bridge.start({ listen: false });
	fake.emit("serverRequest", {
		id: 7, method: "item/commandExecution/requestApproval",
		params: { threadId: "thread-a" },
	});
	assert.equal(forwarded.length, 1);
	assert.equal(forwarded[0].target, "tuner");
	assert.equal(fake.responses.length, 1);
	assert.equal(fake.responses[0].id, 7);
	assert.match(fake.responses[0].message, /cannot approve/);
	await bridge.stop();
});

test("turn start and completion are the working/idle pair", async () => {
	const { bridge, fake, published } = dispatcherWithRuntime();
	await bridge.start({ listen: false });
	fake.emit("turnStarted", { threadId: "thread-a",
		turn: { id: "turn-1" } });
	assert.deepEqual(published.at(-1), ["working", { session: "thread-a" }]);
	fake.emit("turnCompleted", { threadId: "thread-a",
		turn: { id: "turn-1", status: "completed" } });
	await new Promise((resolve) => setImmediate(resolve));
	assert.ok(published.some(([state]) => state === "idle"),
		JSON.stringify(published));
	await bridge.stop();
});

test("a dropped transport is retrying, never failed and never offline",
	async () => {
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.disconnect();
		const entry = published.find(([state]) => state === "retrying");
		assert.ok(entry, JSON.stringify(published));
		assert.equal(entry[1].cause, "transport");
		assert.ok(!published.some(([state]) =>
			state === "offline" || state === "unknown"),
		"the dispatcher published a state only the authority derives");
		await bridge.stop();
	});

test("stopping says goodbye explicitly and nothing follows it",
	async () => {
		// The disconnect a shutdown causes is the shutdown. Reporting a
		// transport retry after the goodbye would describe a
		// reconnection nobody is going to attempt.
		const { bridge, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		await bridge.stop();
		assert.equal(published.at(-1)[0], "end", JSON.stringify(published));
		assert.equal(published.filter(([state]) => state === "end").length,
			1);
	});

test("a deployment with no identity reports as nobody", async () => {
	// There is no participant to report as, so the dispatcher stays
	// silent rather than guessing one from a target name. This runs
	// the REAL factory, so it is the default path being asserted.
	const attempts = [];
	const fake = new FakeClient();
	const bridge = new EventBridge({
		config: anonymousConfig(),
		logger: { ...quiet,
			warn: (line) => attempts.push(line) },
		clientFactory: () => fake,
	});
	await bridge.start({ listen: false });
	fake.emit("turnStarted", { threadId: "thread-b",
		turn: { id: "turn-2" } });
	fake.disconnect();
	await bridge.stop();
	assert.ok(!attempts.some((line) => /runtime/.test(line)),
		attempts.join(" | "));
});

test("the dispatcher never queries a provider to publish state",
	async () => {
		// The no-auto-query boundary: everything published came from an
		// event the dispatcher already received. Nothing here reads a
		// model, a quota or a session from the provider, and nothing
		// wakes the agent to ask.
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("turnStarted", { threadId: "thread-a",
			turn: { id: "turn-1" } });
		for (const [kind, options] of published) {
			// The inventory is its own shape and is asserted by its own
			// cases; this one is about the STATE reports carrying
			// nothing a provider had to be asked for.
			if (kind === "facts") continue;
			for (const key of Object.keys(options ?? {})) {
				assert.ok(["session", "cause", "detail", "work",
				           "episode", "rationale"].includes(key), key);
			}
		}
		await bridge.stop();
	});

// -- R9/R10/R11: identity metadata, classification, renewal ------------------

test("configured runtime identity and action owner are carried, not guessed",
	async () => {
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "acp", provider: "Anthropic", model: "claude-opus-5",
			actionOwner: "baton.slaw", incarnation: "run-1",
			execute: seen.execute });
		await publisher.start();
		const sent = operands(seen.calls[0]);
		assert.equal(sent.provider, "Anthropic");
		assert.equal(sent.model, "claude-opus-5");
		assert.equal(sent["action-owner"], "baton.slaw");
	});

test("a failure is classified into the category an operator can act on",
	async () => {
		// R10: `transport` for an expired credential or a spent quota
		// leaves an operator with nothing to do about it.
		const cases = [
			["401 Unauthorized from the provider", "credential"],
			["invalid_api_key", "credential"],
			["429 rate_limit_exceeded", "limit"],
			["quota exhausted for this key", "limit"],
			["503 provider overloaded", "provider"],
			["ECONNRESET while streaming", "transport"],
			["socket hang up", "transport"],
			["cannot parse the agent's reply", "internal"],
		];
		for (const [message, expected] of cases) {
			const { cause, detail } = classifyFailure(new Error(message));
			assert.equal(cause, expected, message);
			assert.ok(!detail.includes(message),
				"the upstream message was retained in the detail");
		}
	});

test("classification reads the upstream text and never persists it",
	async () => {
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "acp", execute: seen.execute });
		await publisher.start();
		await publisher.state("failed", classifyFailure(new Error(
			"401 from https://user:hunter2@api.example.com/v1?key=abcd")));
		const detail = operands(seen.calls[1]).detail;
		assert.equal(operands(seen.calls[1]).cause, "credential");
		assert.doesNotMatch(detail, /hunter2|abcd|api\.example\.com/);
	});

test("a clean exit carries no failure cause", async () => {
	// The authority's own documentation: a runner that exited cleanly
	// did not fail, and `internal` is an observed internal failure.
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	await publisher.start();
	await publisher.end({ detail: "dispatcher stopped" });
	const sent = operands(seen.calls.at(-1));
	assert.equal(sent.cause, undefined,
		"a clean shutdown was reported as a failure");
	assert.equal(sent.detail, "dispatcher stopped");
});

// A deterministic timer, so renewal is tested by advancing time rather
// than by waiting for it.
function clock() {
	let pending = null;
	return {
		setTimer: (fn) => { pending = fn; return { unref() {} }; },
		clearTimer: () => { pending = null; },
		async tick() {
			const fn = pending;
			pending = null;
			if (fn) fn();
			await new Promise((resolve) => setImmediate(resolve));
			await new Promise((resolve) => setImmediate(resolve));
		},
		armed: () => pending !== null,
	};
}

test("an idle runner renews its lease without asking anything", async () => {
	// R11: the lease is bounded on purpose, and a live-but-quiet runner
	// is not an absent one. Renewal re-states what was LAST OBSERVED.
	const seen = recorder();
	const timer = clock();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "acp", execute: seen.execute, renewMs: 1000,
		setTimer: timer.setTimer, clearTimer: timer.clearTimer });
	await publisher.start({ session: "sess-1" });
	assert.ok(timer.armed(), "no renewal was scheduled");
	await timer.tick();
	const renewal = operands(seen.calls.at(-1));
	assert.equal(seen.calls.at(-1).args[4], "runtime-state");
	assert.equal(renewal.state, "idle");
	// Exactly the same three verbs the adapter already uses: nothing
	// here reads a provider or wakes a model.
	assert.deepEqual([...new Set(verbs(seen.calls))],
		["runtime-start", "runtime-state"]);
});

test("a long turn renews as working rather than expiring into unknown",
	async () => {
		const seen = recorder();
		const timer = clock();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "acp", execute: seen.execute, renewMs: 1000,
			setTimer: timer.setTimer, clearTimer: timer.clearTimer });
		await publisher.start();
		await publisher.state("working", { work: "b0-W7", episode: 3 });
		await timer.tick();
		const renewal = operands(seen.calls.at(-1));
		assert.equal(renewal.state, "working");
		assert.equal(renewal.work, "b0-W7");
		assert.equal(renewal.episode, "3",
			"the renewal lost the episode it was serving");
	});

test("renewal stops at goodbye", async () => {
	const seen = recorder();
	const timer = clock();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute, renewMs: 1000,
		setTimer: timer.setTimer, clearTimer: timer.clearTimer });
	await publisher.start();
	await publisher.end();
	assert.equal(timer.armed(), false, "a closed lease kept renewing");
	await timer.tick();
	assert.equal(verbs(seen.calls).filter((verb) =>
		verb === "runtime-state").length, 0);
});

test("a lease whose opening failed is re-established by the next report",
	async () => {
		// R6's other half: startup stays retryable AND later reports do
		// not write at a lease that was never opened.
		const calls = [];
		let failStart = true;
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", logger: quiet,
			execute: async (_file, args) => {
				calls.push(args[4]);
				if (args[4] === "runtime-start" && failStart) {
					failStart = false;
					throw new Error("authority not ready");
				}
				return { stdout: "{}", stderr: "" };
			},
		});
		assert.equal(await publisher.start(), false);
		await publisher.state("working");
		assert.deepEqual(calls,
			["runtime-start", "runtime-start", "runtime-state"],
			"the report wrote at a lease that was never opened");
	});

test("each observed transition and each renewal has its own identity",
	async () => {
		// R12's other half. Distinct events need distinct ids or the
		// authority replays a committed result — and a renewal that
		// replayed would renew nothing, which is the one thing it is
		// for.
		const seen = recorder();
		const timer = clock();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", incarnation: "run-1", execute: seen.execute,
			renewMs: 1000, setTimer: timer.setTimer,
			clearTimer: timer.clearTimer });
		await publisher.start();
		await publisher.state("working");
		await publisher.state("idle");
		await timer.tick();
		await publisher.end();
		const ids = seen.calls.map((call) => operands(call)["op-id"]);
		assert.equal(new Set(ids).size, ids.length,
			`two logical events shared one identity: ${ids.join(",")}`);
		assert.equal(ids[0], "run-1:start");
		assert.equal(ids.at(-1), "run-1:end");
	});

test("bounded recovery stops instead of retrying forever", async () => {
	// R13 says BOUNDED. A permanently unreachable authority stops being
	// written to; the participant then reports no runtime state at all,
	// which is the honest picture of a runner whose telemetry cannot
	// reach it — and readiness is still untouched.
	const warnings = [];
	let attempts = 0;
	let scheduled = null;
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex",
		logger: { ...quiet, warn: (line) => warnings.push(line) },
		renewMs: 10,
		maxRecoveries: 2,
		setTimer: (callback) => { scheduled = callback; return { unref() {} }; },
		clearTimer: () => { scheduled = null; },
		execute: async () => {
			attempts += 1;
			throw new Error("authority unreachable");
		},
	});
	assert.equal(await publisher.start(), false);
	for (let round = 0; round < 5 && scheduled; round += 1) {
		const fire = scheduled;
		scheduled = null;
		fire();
		await new Promise((resolve) => setImmediate(resolve));
		await new Promise((resolve) => setImmediate(resolve));
	}
	assert.equal(attempts, 3, "recovery was not bounded at two retries");
	assert.ok(warnings.some((line) => /until the adapter restarts/.test(line)),
		warnings.join(" | "));
});

test("recovery stops at goodbye", async () => {
	let attempts = 0;
	let scheduled = null;
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", logger: quiet, renewMs: 10,
		setTimer: (callback) => { scheduled = callback; return { unref() {} }; },
		clearTimer: () => { scheduled = null; },
		execute: async () => {
			attempts += 1;
			throw new Error("authority unreachable");
		},
	});
	await publisher.start();
	await publisher.end();
	const before = attempts;
	scheduled?.();
	await new Promise((resolve) => setImmediate(resolve));
	assert.equal(attempts, before, "a closed lease kept trying to open");
});

test("a later start cannot rewrite the operation the first one issued",
	async () => {
		// R14, from the third direction the reviewer's two cases leave
		// open: an explicit retry with different arguments. The first
		// issue may already have committed, so its operands are the
		// operation — a caller arriving later does not get to change
		// what it was.
		const calls = [];
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			logger: quiet,
			execute: async (_file, args) => {
				calls.push(operands({ args }));
				if (calls.length === 1) throw new Error("result lost");
				return { stdout: "{}", stderr: "" };
			},
		});
		assert.equal(await publisher.start({ session: "launch-session",
			rationale: "the first reason" }), false);
		assert.equal(await publisher.start({ session: "another-session",
			rationale: "a different reason" }), true);
		assert.deepEqual(calls[1], calls[0],
			"a second start rewrote the effectively-once operation");
		assert.equal(calls[0].rationale, "the first reason");
		assert.equal(calls[0].session, "launch-session");
	});

// -- W93 slice 6: the safe operational inventory -----------------------------

test("the inventory publishes locators the deployment already knows",
	async () => {
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", incarnation: "run-1",
			execute: seen.execute });
		await publisher.start();
		await publisher.facts({
			dispatcher: "local/driftquery",
			readiness: "/run/baton.sock",
			workdir: "/home/op/src/baton",
			version: "codex-event-bridge 1.4.0",
		}, { source: "configured" });
		const call = seen.calls.at(-1);
		assert.equal(call.args[4], "runtime-facts");
		const sent = operands(call);
		assert.equal(sent.source, "configured");
		assert.match(sent["observed-at"],
			/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/,
			"the publisher fell back to authority commit time");
		assert.equal(sent.dispatcher, "local/driftquery");
		assert.equal(sent.workdir, "/home/op/src/baton");
		assert.ok(sent["op-id"].startsWith("run-1:f"));
	});

test("the inventory is scrubbed before it leaves the adapter too",
	async () => {
		// The authority refuses a secret-shaped value outright; this is
		// the belt to that braces, because the adapter should not be
		// sending one in the first place.
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", execute: seen.execute });
		await publisher.start();
		await publisher.facts({
			log: "/var/log/x.log token=abcdefghijklmnopqrstuvwxyz012345",
		});
		assert.doesNotMatch(operands(seen.calls.at(-1)).log,
			/abcdefghijklmnopqrstuvwxyz012345/);
	});

test("an empty inventory publishes nothing", async () => {
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", execute: seen.execute });
	await publisher.start();
	assert.equal(await publisher.facts({}), false);
	assert.equal(await publisher.facts({ workdir: undefined }), false);
	assert.deepEqual(verbs(seen.calls), ["runtime-start"]);
});

test("the inventory queues behind the lease like every other write",
	async () => {
		const calls = [];
		let releaseStart;
		const gate = new Promise((resolve) => { releaseStart = resolve; });
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex",
			execute: async (_file, args) => {
				calls.push(args[4]);
				if (args[4] === "runtime-start") await gate;
				return { stdout: "{}", stderr: "" };
			},
		});
		const starting = publisher.start();
		const publishing = publisher.facts({ version: "1.0.0" });
		await new Promise((resolve) => setImmediate(resolve));
		assert.deepEqual(calls, ["runtime-start"]);
		releaseStart();
		await Promise.all([starting, publishing]);
		assert.deepEqual(calls, ["runtime-start", "runtime-facts"]);
	});

test("the dispatcher's production startup publishes what it knows",
	async () => {
		// R17: the real start() path, not the publisher in isolation.
		const { bridge, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		const entry = published.find(([kind]) => kind === "facts");
		assert.ok(entry, JSON.stringify(published));
		const [, sent] = entry;
		assert.match(sent.service, /codex-event-bridge pid \d+/);
		assert.equal(sent.dispatcher, "local/tuner");
		assert.equal(sent.source, "configured");
		// Nothing it cannot observe is invented.
		assert.equal(sent.version, undefined);
		assert.equal(sent.workdir, undefined);
		await bridge.stop();
	});

// W93 review R21: the whole Codex path, from a canonical `wait`
// envelope to the lease-owning dispatcher publishing facts. The
// readiness producer and the dispatcher are separate PROCESSES joined
// by one Unix socket, so a refresh answered by neither is exactly the
// gap round 1 shipped: the producer saw the request and dropped it,
// and the dispatcher that owned the lease never heard of it. Nothing
// below injects a refresh-specific call — the producer runs its own
// loop, the transport is the real socket, and the only thing faked is
// the `baton` executable at each end.
test("a refresh crosses from wait to the dispatcher with no model turn",
	async () => {
		const temporary = await import("node:fs/promises");
		const os = await import("node:os");
		const path = await import("node:path");
		const directory = await temporary.mkdtemp(
			path.join(os.tmpdir(), "codex-runtime-refresh-"));
		const socket = path.join(directory, "events.sock");
		const seen = recorder();
		const { bridge, fake } = dispatcherWithRuntime({
			config: identifiedConfig(socket),
			runtimeFactory: () => new RuntimePublisher(BATON, {
				adapter: "codex", incarnation: "run-1",
				execute: seen.execute, logger: quiet }),
		});
		const controller = new AbortController();
		try {
			await bridge.start({ listen: true });
			const asked = {
				kind: "runtime_refresh",
				action_key: "runtime-refresh:run-1:7",
				incarnation: "run-1",
				generation: 7,
				requested_at: "2026-08-19T11:00:00Z",
				wakes_model: false,
			};
			const envelope = {
				protocol_version: 11, projection_version: "12.2",
				participant: "baton.tuner",
				authority_uuid: "7ba67cb8585dcfd250799fe0dc16e3fa",
				snapshot_seq: 42,
				result: { actionable: [asked], timed_out: false },
			};
			const producer = codexBatonBridge({
				baton: "/opt/baton/bin/baton",
				config: "/home/op/baton.json",
				participant: "baton.tuner",
				target: "tuner", socket, "retry-ms": "5",
			}, {
				signal: controller.signal,
				logger: quiet,
				execute: async () => ({ stdout: JSON.stringify(envelope) }),
			});
			const deadline = Date.now() + 2000;
			while (verbs(seen.calls).filter((verb) => verb === "runtime-facts").length < 2
					&& Date.now() < deadline) {
				await new Promise((resolve) => setTimeout(resolve, 5));
			}
			controller.abort();
			await producer;
			// two publications: the startup inventory, then the one the
			// operator asked for.
			const facts = seen.calls.filter(
				(call) => call.args[4] === "runtime-facts");
			assert.equal(facts.length, 2, verbs(seen.calls).join(","));
			const sent = operands(facts.at(-1));
			assert.equal(sent.incarnation, "run-1");
			assert.equal(sent.dispatcher, "local/tuner");
			assert.equal(sent.readiness, socket);
			// R25: the exact generation crossed both processes.
			assert.equal(sent.answers, "7");
			// R23 on the real path: the adapter's own observation
			// instant, not the authority's commit time.
			assert.match(sent["observed-at"],
				/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
			// and the model was never involved: nothing queued, no turn.
			assert.equal(bridge.globalQueueDepth, 0);
			assert.equal(fake.starts.length, 0);
		} finally {
			controller.abort();
			await bridge.stop();
			await temporary.rm(directory, { recursive: true, force: true });
		}
	});

test("the dispatcher answers a refresh for the participant it IS",
	async () => {
		const { bridge, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		published.length = 0;
		const answer = await bridge.handleRequest({
			control: "runtime-refresh", target: "tuner",
			participant: "baton.tuner", incarnation: "run-1",
			generation: 7, requested_at: "2026-08-19T11:00:00Z" });
		assert.equal(answer.accepted, true);
		assert.equal(answer.reason, "runtime-refresh");
		const [, sent] = published.find(([kind]) => kind === "facts");
		assert.equal(sent.answers, 7, "the generation was not carried");
		assert.equal(published.filter(([kind]) => kind === "facts").length, 1);
		assert.equal(bridge.globalQueueDepth, 0);
		await bridge.stop();
	});

test("a refresh addressed to somebody else is refused, not answered",
	async () => {
		// Publishing facts under another participant's identity because
		// a message asked is exactly how a roster starts lying.
		const { bridge, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		published.length = 0;
		const answer = await bridge.handleRequest({
			control: "runtime-refresh", target: "tuner",
			participant: "baton.other", incarnation: "run-1" });
		assert.equal(answer.accepted, false);
		assert.equal(answer.reason, "foreign-participant");
		assert.deepEqual(published, []);
		await bridge.stop();
	});

test("a refresh for an unknown target is refused", async () => {
	const { bridge } = dispatcherWithRuntime();
	await bridge.start({ listen: false });
	const answer = await bridge.handleRequest({
		control: "runtime-refresh", target: "ghost",
		participant: "baton.tuner" });
	assert.equal(answer.accepted, false);
	assert.equal(answer.reason, "unknown-target");
	await bridge.stop();
});

test("a refresh whose publication failed is not called answered",
	async () => {
		// The request still stands, and the producer's retry is the
		// only thing that will answer it.
		const { bridge } = dispatcherWithRuntime({
			runtimeFactory: () => ({
				incarnation: "run-1",
				async start() {}, async state() {}, async incident() {}, async end() {},
				async facts() { return false; },
			}),
		});
		await bridge.start({ listen: false });
		const answer = await bridge.handleRequest({
			control: "runtime-refresh", target: "tuner",
			participant: "baton.tuner" });
		assert.equal(answer.accepted, false);
		assert.equal(answer.reason, "runtime-refresh-failed");
		await bridge.stop();
	});

// -- W93 review R26: the startup inventory outlives a delayed lease ---------

function clockFrom(instants) {
	// Whole seconds, advanced explicitly. The bug this covers is a
	// SECOND BOUNDARY crossed while the lease was still opening, so a
	// clock that cannot cross one cannot see it.
	let at = 0;
	return {
		tick: () => { at = Math.min(at + 1, instants.length - 1); },
		now: () => new Date(instants[at]),
	};
}

test("a startup inventory delayed past the lease open is still published",
	async () => {
		// The dispatcher deliberately does not await start() or
		// facts(). If lease open is slow — or fails and recovers — the
		// facts task eventually runs with an instant EARLIER than the
		// authority's started_ts, and the authority is right to refuse
		// a fact older than the launch it describes. The publisher
		// floors its own instant at the lease it actually opened.
		const clock = clockFrom([
			"2026-08-19T10:00:00.400Z", "2026-08-19T10:00:02.100Z"]);
		const calls = [];
		let releaseStart;
		const gate = new Promise((resolve) => { releaseStart = resolve; });
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", incarnation: "run-1", logger: quiet,
			now: clock.now,
			execute: async (_file, args) => {
				if (args[4] === "runtime-start") await gate;
				calls.push(args);
				return { stdout: "{}", stderr: "" };
			},
		});
		const starting = publisher.start();
		// collected NOW, while the lease is still opening
		const publishing = publisher.facts({ version: "1.4.0" },
			{ source: "configured" });
		await new Promise((resolve) => setImmediate(resolve));
		clock.tick();
		releaseStart();
		await Promise.all([starting, publishing]);
		const sent = operands({ args: calls.at(-1) });
		assert.equal(calls.at(-1)[4], "runtime-facts");
		assert.equal(sent["observed-at"], "2026-08-19T10:00:02Z",
			"the inventory would have been refused as older than its lease");
	});

test("a genuinely older observation keeps its own instant", async () => {
	// The floor exists for facts handed over before the lease opened,
	// not to relabel every old observation as fresh: an adapter that
	// states when it read something is believed.
	const clock = clockFrom(["2026-08-19T10:00:00.000Z"]);
	const seen = recorder();
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", incarnation: "run-1", logger: quiet,
		now: clock.now, execute: seen.execute });
	await publisher.start();
	await publisher.facts({ version: "1.4.0" },
		{ observedAt: "2026-08-19T09:59:00Z" });
	assert.equal(operands(seen.calls.at(-1))["observed-at"],
		"2026-08-19T09:59:00Z");
});

test("a recovery re-floors the instant on its NEW lease", async () => {
	// A recovered lease has a new started_ts, and anything still queued
	// behind it is observed no earlier than that.
	const clock = clockFrom([
		"2026-08-19T10:00:00.000Z", "2026-08-19T10:00:05.000Z"]);
	const calls = [];
	let attempt = 0;
	const publisher = new RuntimePublisher(BATON, {
		adapter: "codex", incarnation: "run-1", logger: quiet,
		now: clock.now,
		execute: async (_file, args) => {
			if (args[4] === "runtime-start" && attempt++ === 0) {
				throw new Error("authority unreachable");
			}
			calls.push(args);
			return { stdout: "{}", stderr: "" };
		},
	});
	await publisher.start();
	assert.equal(publisher.started, false, "the lease opened after all");
	clock.tick();
	await publisher.facts({ version: "1.4.0" }, { source: "configured" });
	const facts = calls.filter((args) => args[4] === "runtime-facts");
	assert.equal(facts.length, 1);
	assert.equal(operands({ args: facts[0] })["observed-at"],
		"2026-08-19T10:00:05Z");
});

test("fact publications queued together keep distinct operation identities",
	async () => {
		// The dispatcher intentionally hands startup facts to the publisher
		// without awaiting them. A refresh can therefore arrive while that
		// publication is still queued. Each fact event needs the identity it
		// received when it was issued; reading the publisher's later shared
		// sequence from inside the queue turns the second event into a
		// mismatched replay of the first.
		const seen = recorder();
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", incarnation: "run-1", logger: quiet,
			execute: seen.execute,
		});
		await publisher.start();
		const startup = publisher.facts({ version: "1.4.0" },
			{ source: "configured" });
		const refresh = publisher.facts({ version: "1.4.1" },
			{ source: "configured", answers: 7 });
		await Promise.all([startup, refresh]);
		const factCalls = seen.calls.filter(
			(call) => call.args[4] === "runtime-facts");
		assert.equal(factCalls.length, 2);
		const identities = factCalls.map(
			(call) => operands(call)["op-id"]);
		assert.equal(new Set(identities).size, 2,
			`queued facts reused ${identities.join(", ")}`);
	});

test("a refresh answered while the startup inventory is still queued",
	async () => {
		// R27 as the DEPLOYMENT meets it. `start()` publishes the
		// inventory without awaiting it; a refresh arriving in that
		// window is a second publication issued before the first has
		// run. Both must reach the authority as distinct operations —
		// otherwise the refresh is refused as a mismatched replay and
		// the operator's question stays open although the adapter
		// answered it.
		const seen = recorder();
		let releaseStart;
		const gate = new Promise((resolve) => { releaseStart = resolve; });
		const publisher = new RuntimePublisher(BATON, {
			adapter: "codex", incarnation: "run-1", logger: quiet,
			execute: async (file, args) => {
				if (args[4] === "runtime-start") await gate;
				return await seen.execute(file, args);
			},
		});
		const { bridge } = dispatcherWithRuntime({
			runtimeFactory: () => publisher });
		try {
			await bridge.start({ listen: false });
			const answering = bridge.handleRequest({
				control: "runtime-refresh", target: "tuner",
				participant: "baton.tuner", incarnation: "run-1",
				generation: 7 });
			releaseStart();
			const answer = await answering;
			assert.equal(answer.accepted, true);
			const identities = seen.calls
				.filter((call) => call.args[4] === "runtime-facts")
				.map((call) => operands(call)["op-id"]);
			assert.equal(identities.length, 2);
			assert.equal(new Set(identities).size, 2,
				`the queued publications reused ${identities.join(", ")}`);
		} finally {
			await bridge.stop();
		}
	});

// -- W415: the denial also files a DURABLE incident -------------------------
//
// `work/records/2026/08/finding-managed-turn-approval-incidents/`. The
// `waiting-input` state above is correct and TRANSIENT — it is supposed
// to vanish when the runner returns to idle. That is exactly what erased
// the evidence three times: the turn ended, the lease moved on, the
// Inbox row went with it, and the Work sat unclaimed with the only
// explanation in a rollout nobody reads. These pin the other half.

test("W415: a denied approval files a durable incident beside the state",
	async () => {
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("serverRequest", {
			id: 7, method: "item/commandExecution/requestApproval",
			params: { threadId: "thread-a" },
		});
		// BOTH, not one or the other: they answer different questions.
		assert.ok(published.some(([state]) => state === "waiting-input"),
			"the transient runtime state is still published");
		const filed = published.find(([kind]) => kind === "incident");
		assert.ok(filed, `no incident filed: ${JSON.stringify(published)}`);
		assert.equal(filed[1].cause, "approval");
		assert.equal(filed[1].category, "shell");
		assert.equal(filed[1].session, "thread-a");
		assert.match(filed[1].detail, /non-interactive/);
		await bridge.stop();
	});

test("W415: the incident carries no command body, argv or environment",
	async () => {
		// An approval payload can carry credentials, environment values
		// and file contents. What travels is the closed safe category
		// and a detail naming the METHOD only.
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("serverRequest", {
			id: 7, method: "item/commandExecution/requestApproval",
			params: {
				threadId: "thread-a",
				command: ["/bin/bash", "-lc", "baton --config /secret claim"],
				cwd: "/home/sl/src/baton",
				env: { ANTHROPIC_API_KEY: "sk-ant-secret-value" },
			},
		});
		const filed = published.find(([kind]) => kind === "incident");
		const serialized = JSON.stringify(filed[1]);
		for (const leaked of ["/bin/bash", "-lc", "sk-ant", "ANTHROPIC",
		                      "/secret", "claim"]) {
			assert.ok(!serialized.includes(leaked),
				`the incident leaked ${leaked}: ${serialized}`);
		}
		await bridge.stop();
	});

test("W415: the incident correlates with the episode the turn was serving",
	async () => {
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		// A turn is in flight for a readiness episode. The Work and
		// episode ride BESIDE the action key, because the key is
		// delivered whole and never parsed.
		fake.emit("turnStarted", { threadId: "thread-a", turn: { id: "turn-1" } });
		bridge.targetByThread.get("local\u0000thread-a").activeTurn = {
			id: "turn-1",
			event: { action: { participant: "baton.tuner",
				key: "work:5f7-W415:9:g1", work: "5f7-W415", episode: 9 } },
		};
		fake.emit("serverRequest", {
			id: 8, method: "item/commandExecution/requestApproval",
			params: { threadId: "thread-a" },
		});
		const filed = published.find(([kind]) => kind === "incident");
		assert.equal(filed[1].work, "5f7-W415");
		assert.equal(filed[1].episode, 9);
		assert.equal(filed[1].actionKey, "work:5f7-W415:9:g1");
		await bridge.stop();
	});

test("W415: with no turn in flight the incident still files, uncorrelated",
	async () => {
		// A locator-less incident is worth less than a correlated one and
		// far more than none: the operator still learns the turn failed.
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("serverRequest", {
			id: 9, method: "item/commandExecution/requestApproval",
			params: { threadId: "thread-a" },
		});
		const filed = published.find(([kind]) => kind === "incident");
		assert.ok(filed);
		assert.equal(filed[1].work, null);
		assert.equal(filed[1].episode, null);
		await bridge.stop();
	});

test("W415: the approval method maps to a closed safe category", async () => {
	const cases = [
		["item/commandExecution/requestApproval", "shell"],
		["execCommandApproval", "shell"],
		["applyPatchApproval", "patch"],
		["item/fileChange/requestApproval", "patch"],
		["permissionsRequestApproval", "file-write"],
		["mcpServerElicitationRequest", "mcp"],
		["something/entirely/new", "other"],
	];
	for (const [method, expected] of cases) {
		const { bridge, fake, published } = dispatcherWithRuntime();
		await bridge.start({ listen: false });
		fake.emit("serverRequest", { id: 7, method,
			params: { threadId: "thread-a" } });
		const filed = published.find(([kind]) => kind === "incident");
		assert.equal(filed[1].category, expected,
			`${method} should map to ${expected}`);
		await bridge.stop();
	}
});

// -- W415 round 1: the incident trigger survives the real fix ---------------
//
// The review's sharpest point: `approvalPolicy: never` would have
// removed the only trigger the durable incident has, leaving the Work
// unclaimed and silent again — the exact original defect, differently
// spelled. The narrow writable root fixes the cause instead, and the
// approval path stays observable so an UNEXPECTED escalation still
// produces both the transient state and the sticky incident.

test("W415: the dispatcher never suppresses the approval request it reports on",
	async () => {
		const { validateConfig } = await import("../src/config.mjs");
		const config = validateConfig({
			roleInstructions: { binary: "/opt/baton/bin/baton",
				config: "/srv/baton/baton.json",
			execPolicyFile: FIXTURE_POLICY },
			servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
			targets: { tuner: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.tuner", role: "tuner",
					actionOwner: "ops.slaw" } } },
			eventSocket: "/tmp/codex-event-bridge-w415-unused.sock",
			quarantineDir: freshQuarantineDir(),
		});
		const { bridge, fake, published } = dispatcherWithRuntime({ config });
		await bridge.start({ listen: false });
		fake.emit("serverRequest", {
			id: 7, method: "item/commandExecution/requestApproval",
			params: { threadId: "thread-a" },
		});
		// Still both: the transient state AND the durable incident.
		assert.ok(published.some(([state]) => state === "waiting-input"));
		assert.ok(published.some(([kind]) => kind === "incident"),
			`the incident trigger was lost: ${JSON.stringify(published)}`);
		// Still denied, never approved.
		assert.equal(fake.responses.length, 1);
		assert.match(fake.responses[0].message, /cannot approve/);
		await bridge.stop();
	});

test("W415: a managed deployment must name an action owner to be startable",
	async () => {
		const { validateConfig } = await import("../src/config.mjs");
		const base = {
			roleInstructions: { binary: "/opt/baton/bin/baton",
				config: "/srv/baton/baton.json",
			execPolicyFile: FIXTURE_POLICY },
			servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
			targets: { tuner: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.tuner", role: "tuner",
					actionOwner: "ops.slaw" } } },
			eventSocket: "/tmp/codex-event-bridge-w415-unused.sock",
			quarantineDir: freshQuarantineDir(),
		};
		assert.doesNotThrow(() => validateConfig(base));
		// The deployment that REPRODUCED this defect had no action owner,
		// so it could not have raised the incident this Work adds. That
		// now fails validation rather than warning into a log nobody
		// reads — which is the invisibility being fixed.
		const ownerless = JSON.parse(JSON.stringify(base));
		delete ownerless.targets.tuner.identity.actionOwner;
		assert.throws(() => validateConfig(ownerless),
			/needs identity.actionOwner so a failed turn can raise a durable incident/);
		// And a managed deployment must name the policy that authorizes it.
		const unpoliced = JSON.parse(JSON.stringify(base));
		delete unpoliced.roleInstructions.execPolicyFile;
		assert.throws(() => validateConfig(unpoliced),
			/execPolicyFile must be a non-empty string/);
	});

test("W415: two observed approvals are two publications, not one replay",
	async () => {
		// Review round 2 P2: the operation id was derived from
		// (cause, category, work, episode), so a SECOND approval request
		// in the same episode replayed the first committed result. It
		// never reached the authority's coalescing update and
		// `occurrences` stayed at 1 — losing exactly the count that says
		// a repair did not hold.
		const { RuntimePublisher } = await import("../src/runtime_publisher.mjs");
		const calls = [];
		const publisher = new RuntimePublisher(
			{ binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json",
			  participant: "baton.tuner" },
			{ incarnation: "run-1", adapter: "codex", actionOwner: "ops.slaw",
			  logger: quiet,
			  execute: async (_file, argv) => { calls.push(argv); return { stdout: "{}" }; } });

		const observation = { cause: "approval", category: "shell",
		                      work: "aaa-W2", episode: 4 };
		await publisher.incident(observation);
		await publisher.incident({ ...observation });

		const incidents = calls.filter((argv) => argv.includes("incident"));
		assert.equal(incidents.length, 2, "both observations must be published");
		const ids = incidents.map((argv) =>
			argv.find((operand) => operand.startsWith("op-id=")));
		assert.notEqual(ids[0], ids[1],
			`two observed approvals shared one operation id (${ids[0]}), so the `
			+ `second would replay instead of incrementing the count`);
		// Every operand except the identity is the same, which is what
		// makes the authority coalesce them into one incident.
		const withoutId = (argv) => argv.filter((o) => !o.startsWith("op-id="));
		assert.deepEqual(withoutId(incidents[0]), withoutId(incidents[1]));
	});

// -- W415: the deployment-owned exact command policy ---------------------
//
// W220 (`finding-managed-turn-workflow-policy`, 2026-08-21) superseded
// the four-verb ruling AS TO THE VERB SET ONLY. Everything W415
// established about HOW the policy works — deployment-owned generation,
// exact binary/config/participant matching, broad-rule refusal,
// extra-verb refusal, no raw store access — is unchanged and still
// asserted below.
//
// The expected capability is written out HERE rather than read from the
// implementation. Round-4 review: asserting that every member of the
// implementation's own list generated a rule cannot catch the
// implementation WIDENING that list, which is exactly what happened
// when `mark-seen` was added on an implementer's judgement. That lesson
// survives the ruling that later added `mark-seen` deliberately.
const MANAGED_WORKFLOW = [
	"create", "accept", "respond", "dispose", "close", "block", "unblock",
	"mark-seen", "classify", "claim", "release", "prioritize", "pass",
	"heartbeat", "phase", "try", "extend", "report", "assess", "abandon",
	"revise", "start-thread", "say", "label", "unlabel", "bind", "poke",
	"poke-answer", "poke-cancel", "reroute",
];
// The public mutations the profile deliberately excludes. Written out
// here for the same reason as the profile itself.
const EXCLUDED = ["activate", "regen", "runtime-start", "runtime-state",
                  "runtime-end", "runtime-facts", "runtime-refresh",
                  "incident", "dismiss"];

//
// Measured against a live app-server on 2026-08-20, and the reason this
// is command policy rather than a filesystem grant:
//   - a DIRECTORY writable root lets any shell command in the turn
//     rewrite or delete `work.sqlite3` AND `baton.json` (an unrelated
//     `printf >> baton.json` succeeded, with no approval request);
//   - a FILE or GLOB root is echoed back and grants nothing at all.
// A prefix rule is command-aware: `rm work.sqlite3` matches nothing.

test("W415: the generated rules name the executable, config, participant and verb",
	async () => {
		const { rulesFor, RULED_VERBS } = await import("../src/exec_policy.mjs");
		const identity = { binary: "/opt/baton/bin/baton",
			config: "/srv/baton/baton.json", participant: "baton.codex" };
		// The APPROVED set, in the ruled order, compared against the
		// literal above rather than against the implementation's own list.
		assert.deepEqual(RULED_VERBS, MANAGED_WORKFLOW,
			"the ruled capability is exactly the confirmed managed-workflow "
			+ "profile; adding one verb is a ruling to obtain, not an "
			+ "implementation decision");
		const rules = rulesFor(identity);
		assert.equal(rules.length, MANAGED_WORKFLOW.length);
		for (const verb of MANAGED_WORKFLOW) {
			assert.ok(rules.some((rule) => rule.includes(`"${verb}"`)),
				`no rule for ${verb}`);
		}
		// W220: the operation whose absence stranded a claimed Work is in
		// the set now, and the workflow that follows it is complete.
		for (const verb of ["mark-seen", "respond", "release", "heartbeat"]) {
			assert.ok(rules.some((rule) => rule.includes(`"${verb}"`)),
				`the managed workflow cannot complete without ${verb}`);
		}
		// And every deliberately EXCLUDED mutation is authorized by none
		// of them: deployment, adapter-owned runtime publication, and
		// dispatcher-owned incident publication stay outside the profile.
		for (const unlisted of EXCLUDED) {
			assert.ok(!rules.some((rule) => rule.includes(`"${unlisted}"`)),
				`${unlisted} is excluded from the profile and must have no rule`);
		}
		for (const rule of rules) {
			assert.ok(rule.includes(identity.binary));
			assert.ok(rule.includes(identity.config));
			assert.ok(rule.includes(identity.participant));
			assert.ok(rule.endsWith('decision="allow")'));
		}
		// A relative executable matches a different command depending on
		// where the turn happens to be running.
		assert.throws(() => rulesFor({ ...identity, binary: "baton" }),
			/ABSOLUTE installed executable/);
	});

test("W415: a BROAD rule is refused, not counted as coverage", async () => {
	const { auditRules, assertPolicyProvisioned, rulesFor } =
		await import("../src/exec_policy.mjs");
	const { mkdtempSync, writeFileSync } = await import("node:fs");
	const { join } = await import("node:path");
	const identity = { binary: "/opt/baton/bin/baton",
		config: "/srv/baton/baton.json", participant: "baton.codex" };

	// The shape the LIVE deployment actually has: the executable alone.
	// It authorizes every verb this participant can reach, including
	// `regen` and `release`, so it is reported as broad rather than as
	// coverage — the same substitution of a broad capability for a
	// narrow one that this Work has rejected in three other forms.
	const broad = auditRules(
		`prefix_rule(pattern=["${identity.binary}"], decision="allow")\n`, identity);
	assert.equal(broad.missing.length, 0, "it does technically cover them");
	assert.equal(broad.satisfied, false, "but broad coverage is not satisfaction");
	assert.equal(broad.broad.length, MANAGED_WORKFLOW.length);

	const dir = mkdtempSync("/tmp/w415-policy-test-");
	const file = join(dir, "broad.rules");
	writeFileSync(file, `prefix_rule(pattern=["${identity.binary}"], decision="allow")\n`);
	assert.throws(() => assertPolicyProvisioned(file, identity),
		/contains a BROADER rule/);

	// The exact rules satisfy it.
	const exact = join(dir, "exact.rules");
	writeFileSync(exact, `${rulesFor(identity).join("\n")}\n`);
	assert.equal(assertPolicyProvisioned(exact, identity).satisfied, true);

	// A rule for a DIFFERENT participant or config does not cover this one.
	const other = join(dir, "other.rules");
	writeFileSync(other, `${rulesFor({ ...identity, participant: "baton.tuner" })
		.join("\n")}\n`);
	assert.throws(() => assertPolicyProvisioned(other, identity),
		/does not authorize/);

	// A deny rule is never coverage.
	const denied = join(dir, "deny.rules");
	writeFileSync(denied, `${rulesFor(identity).join("\n")
		.replace(/allow/g, "deny")}\n`);
	assert.throws(() => assertPolicyProvisioned(denied, identity),
		/does not authorize/);

	// An unreadable policy is a refusal, not an assumption of coverage.
	assert.throws(() => assertPolicyProvisioned(join(dir, "absent.rules"), identity),
		/is unreadable/);
});

test("W415: the dispatcher refuses to start without a provisioned policy",
	async () => {
		// A dispatcher whose turns escalate on every claim is the defect
		// this Work records; it must not open leases and report itself
		// healthy while in that state.
		const { validateConfig } = await import("../src/config.mjs");
		const { mkdtempSync, writeFileSync } = await import("node:fs");
		const { join } = await import("node:path");
		const dir = mkdtempSync("/tmp/w415-start-");
		const broad = join(dir, "broad.rules");
		writeFileSync(broad,
			'prefix_rule(pattern=["/opt/baton/bin/baton"], decision="allow")\n');
		const config = validateConfig({
			roleInstructions: { binary: "/opt/baton/bin/baton",
				config: "/srv/baton/baton.json", execPolicyFile: broad },
			servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
			targets: { tuner: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.tuner", role: "tuner",
					actionOwner: "ops.slaw" } } },
			eventSocket: "/tmp/codex-event-bridge-w415-unused.sock",
			quarantineDir: freshQuarantineDir(),
		});
		const { bridge } = dispatcherWithRuntime({ config });
		await assert.rejects(() => bridge.start({ listen: false }),
			/contains a BROADER rule/);
	});
test("W415: exact rules do not cancel a broad one that is still present",
	async () => {
		// Round-6 review. `broad` was only recorded when a ruled command
		// had NO exact rule, so the four exact rules plus the retired
		// executable-only rule audited as SATISFIED — and that is the most
		// likely upgrade state: an operator adds the new rules and forgets
		// to remove the old one. The dispatcher would have started while
		// the participant could still invoke every Baton verb.
		const { rulesFor, auditRules, assertPolicyProvisioned } =
			await import("../src/exec_policy.mjs");
		const { mkdtempSync, writeFileSync } = await import("node:fs");
		const { join } = await import("node:path");
		const identity = { binary: "/opt/baton/bin/baton",
			config: "/srv/baton/baton.json", participant: "baton.codex" };
		const exact = rulesFor(identity).join("\n");
		const dir = mkdtempSync("/tmp/w415-mixed-test-");
		const write = (name, text) => {
			const file = join(dir, name);
			writeFileSync(file, `${text}\n`);
			return file;
		};

		// EXACT ONLY still succeeds — the correction must not make the
		// approved state unreachable.
		assert.equal(assertPolicyProvisioned(write("exact.rules", exact),
			identity).satisfied, true);

		// EXACT + BROAD executable: the reviewer's reproduction.
		const mixed = auditRules(
			`${exact}\nprefix_rule(pattern=["${identity.binary}"], decision="allow")`,
			identity);
		assert.deepEqual(mixed.missing, []);
		assert.equal(mixed.broad.length, MANAGED_WORKFLOW.length,
			"every ruled verb is still broadly covered");
		assert.equal(mixed.satisfied, false,
			"a narrow rule does not cancel a broad one; both are simply present");
		assert.throws(() => assertPolicyProvisioned(
			write("mixed.rules",
				`${exact}\nprefix_rule(pattern=["${identity.binary}"], decision="allow")`),
			identity), /half-finished upgrade state/);

		// EXACT + a broad rule at the participant prefix — the other
		// shape that covers every verb without naming one.
		const prefix = `prefix_rule(pattern=["${identity.binary}", "--config", `
			+ `"${identity.config}", "--participant", "${identity.participant}"], `
			+ `decision="allow")`;
		assert.throws(() => assertPolicyProvisioned(
			write("prefix.rules", `${exact}\n${prefix}`), identity),
			/BROADER rule/);

		// BROAD ONLY still refuses, with the install instructions.
		assert.throws(() => assertPolicyProvisioned(
			write("broad.rules",
				`prefix_rule(pattern=["${identity.binary}"], decision="allow")`),
			identity), /install these rules and remove the broad one/);
	});

test("W415: an unruled verb for the same participant fails the preflight",
	async () => {
		// Exact-set clarification, pinned in FINDING.md 2026-08-20: the
		// nominated participant policy IS the approved set, not merely a
		// file that happens to contain it. I had left this advisory
		// because refusing looked like it needed a mutating-verb list
		// maintained here; the ruling dissolves that — read-only commands
		// need no allow rule at all, so any verb outside the set is extra
		// capability whatever it does.
		const { rulesFor, auditRules, assertPolicyProvisioned, RULED_VERBS } =
			await import("../src/exec_policy.mjs");
		const { mkdtempSync, writeFileSync } = await import("node:fs");
		const { join } = await import("node:path");
		const identity = { binary: "/opt/baton/bin/baton",
			config: "/srv/baton/baton.json", participant: "baton.codex" };
		const other = { ...identity, participant: "baton.tuner" };
		const exact = rulesFor(identity).join("\n");
		const dir = mkdtempSync("/tmp/w415-exactset-test-");
		const write = (name, text) => {
			const file = join(dir, name);
			writeFileSync(file, `${text}\n`);
			return file;
		};
		const ruleFor = (who, verb) =>
			`prefix_rule(pattern=["${identity.binary}", "--config", `
			+ `"${identity.config}", "--participant", "${who}", "${verb}"], `
			+ `decision="allow")`;

		// Exact only still succeeds.
		assert.equal(assertPolicyProvisioned(write("exact.rules", exact),
			identity).satisfied, true);

		// Any other verb for THIS participant refuses — mutating or not,
		// because the set is the set. W220: the deliberately excluded
		// deployment, runtime and incident mutations are exactly the
		// verbs this must keep refusing, alongside a pure read.
		for (const verb of [...EXCLUDED, "detail", "wait"]) {
			const policy = `${exact}\n${ruleFor(identity.participant, verb)}`;
			const audit = auditRules(policy, identity);
			assert.deepEqual(audit.extra, [verb]);
			assert.equal(audit.satisfied, false, `${verb} must fail the preflight`);
			assert.throws(() => assertPolicyProvisioned(
				write(`${verb}.rules`, policy), identity),
				/dedicated to the approved 'managed-work-workflow' set/);
		}

		// OTHER participants' rules are independent and stay valid —
		// including their unruled verbs, which are not this
		// participant's capability.
		assert.equal(assertPolicyProvisioned(
			write("other-exact.rules", `${exact}\n${rulesFor(other).join("\n")}`),
			identity).satisfied, true);
		assert.equal(assertPolicyProvisioned(
			write("other-extra.rules", `${exact}\n${ruleFor(other.participant, "regen")}`),
			identity).satisfied, true);

		// W220 round 1: a prefix rule may carry OPERANDS, and the
		// same-identity test used to require a pattern exactly one
		// element longer than the participant prefix. So an excluded
		// verb with any operand slipped through and audited as
		// satisfied. Narrower than a rule the ruling never granted is
		// still capability the ruling never granted.
		const qualified = (who, verb, ...rest) =>
			`prefix_rule(pattern=["${identity.binary}", "--config", `
			+ `"${identity.config}", "--participant", "${who}", "${verb}"`
			+ rest.map((operand) => `, "${operand}"`).join("")
			+ `], decision="allow")`;
		for (const [verb, ...operands] of [
				["regen", "op-id=authorized-extra"],
				["activate", "directory=/srv/baton"],
				["runtime-state", "incarnation=x", "state=working"],
				["dismiss", "incident=3"],
				// An unknown or future verb, and an operand sitting
				// where a verb should be: both are capability the
				// profile never granted, so both fail closed.
				["teleport", "a=b"],
				["op-id=sneaky"]]) {
			const policy = `${exact}\n${qualified(identity.participant, verb,
			                                      ...operands)}`;
			const audit = auditRules(policy, identity);
			assert.deepEqual(audit.extra, [verb],
				`${verb} with operands was not seen as extra capability`);
			assert.equal(audit.satisfied, false, verb);
			assert.throws(() => assertPolicyProvisioned(
				write(`qualified-${verb.replace(/[^a-z-]/g, "")}.rules`, policy),
				identity), /dedicated to the approved 'managed-work-workflow' set/);
		}
		// A RULED verb carrying operands authorizes a SUBSET of a
		// capability the profile already grants, so it is not extra —
		// the test is on the verb slot, which is what the ruling is
		// about.
		assert.equal(assertPolicyProvisioned(
			write("ruled-qualified.rules",
				`${exact}\n${qualified(identity.participant, "claim", "work=W1")}`),
			identity).satisfied, true);
		// And the exact thirty are still accepted on their own.
		assert.equal(assertPolicyProvisioned(write("still-exact.rules", exact),
			identity).satisfied, true);
		// Another participant's operand-qualified rule stays theirs.
		assert.equal(assertPolicyProvisioned(
			write("other-qualified.rules",
				`${exact}\n${qualified(other.participant, "regen", "op-id=x")}`),
			identity).satisfied, true);

		// The refusal names the approved set, so an operator does not
		// have to go looking for it.
		try {
			assertPolicyProvisioned(write("named.rules",
				`${exact}\n${ruleFor(identity.participant, "regen")}`), identity);
			assert.fail("should have refused");
		} catch (error) {
			for (const verb of RULED_VERBS) assert.match(error.message, new RegExp(verb));
			assert.match(error.message, /read-only commands need no allow rule here/);
		}
	});
