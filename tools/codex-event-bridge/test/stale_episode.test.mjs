// W1224: a queued readiness event is revalidated before it becomes a turn.
//
// `work/records/2026/08/finding-readiness-wrong-participant-after-pass/`.
// Live v11 use produced three canonical contradictions: after a
// reviewer passed Work to `baton.impl`, the Codex readiness path woke
// the REVIEWER with "ready and unclaimed for baton.codex" while
// canonical `detail` showed the Work queued at `baton.impl` with no
// handler and no reviewer claim. The claim then failed authorization,
// which is the boundary working — but the wake was a lie the operator
// had to chase.
//
// The projection is not the source: `participant_actions` drops the
// Work from the old participant and offers it to the new endpoint
// under a NEW episode key the moment the pass commits (proved in
// `tests/work/test_w1224_stale_readiness.py`). The window is this
// dispatcher's queue: an event can wait behind a running turn and
// drain after the pass. The ACP bridge already revalidates at exactly
// this point; the Codex path did not.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { normalizeEvent } from "../src/event_types.mjs";
import { actionEvent } from "../src/codex_baton_bridge.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";

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


const quiet = { info() {}, warn() {}, error() {}, debug() {} };
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

class FakeClient extends EventEmitter {
	constructor() {
		super();
		this.connected = true;
		this.starts = [];
	}

	async connectAndInitialize() {
		this.connected = true;
		this.emit("connected", {});
	}

	async startTurn(threadId, text, clientId) {
		this.starts.push({ threadId, text, clientId });
		return { id: `turn-${this.starts.length}`, status: "inProgress" };
	}

	async resume(threadId) {
		return { thread: { id: threadId, status: { type: "idle" }, turns: [] } };
	}

	async readThread(threadId) {
		return { id: threadId, status: { type: "idle" }, turns: [] };
	}

	disconnect() {
		// Emitted, because the dispatcher's connection loop parks on
		// this event and `stop()` awaits that task. A fake that goes
		// quiet instead of saying goodbye hangs the suite rather than
		// the product.
		const wasConnected = this.connected;
		this.connected = false;
		if (wasConnected) this.emit("disconnected");
	}
}

function config(socket = "/tmp/codex-w1224-unused.sock") {
	return validateConfig({
		servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
		targets: {
			tuner: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.tuner", role: "tuner", actionOwner: "ops.slaw" } },
		},
		roleInstructions: { binary: "/opt/baton/bin/baton", config: "/home/op/baton.json",
			execPolicyFile: FIXTURE_POLICY },
		eventSocket: socket,
		quarantineDir: freshQuarantineDir(),
	});
}

/** The producer's own event, so this suite cannot drift from the shape
 *  the dispatcher actually receives. */
function readinessEvent(key = "work:7ba67cb8-W1224:4:g1",
                        participant = "baton.tuner") {
	const envelope = { authority_uuid: UUID, participant,
		result: { actionable: [] } };
	const action = { kind: "work", action_key: key,
		work: "7ba67cb8-W1224", local_id: "W1224", title: "the passed work",
		phase: "queued", claimed: false, episode_seq: 4, config_generation: 1 };
	return actionEvent(envelope, action, { target: "tuner" });
}

function bridge({ revalidate, socket } = {}) {
	const fake = new FakeClient();
	const dispatcher = new EventBridge({
		config: config(socket), logger: quiet,
		clientFactory: () => fake,
		runtimeFactory: () => ({
			incarnation: "run-1", async start() {}, async state() {},
			async incident() {},
			async facts() { return true; }, async end() {},
		}),
		revalidate,
	});
	return { dispatcher, fake };
}

function answering(keys, { fail = false } = {}) {
	const calls = [];
	return {
		calls,
		revalidate: async (file, args) => {
			calls.push({ file, args });
			if (fail) throw new Error("baton unreachable");
			return { stdout: JSON.stringify({
				result: { actionable: keys.map((key) => ({
					kind: "work", action_key: key })) } }) };
		},
	};
}

async function settle(times = 6) {
	for (let index = 0; index < times; index += 1) {
		await new Promise((resolve) => setImmediate(resolve));
	}
}

async function ready(dispatcher, fake) {
	await dispatcher.start({ listen: false });
	// the target must be idle for the queue to drain
	fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
	await settle();
}

// -- the defect --------------------------------------------------------------

test("an episode that ended is dropped instead of becoming a turn",
	async () => {
		const answer = answering([]);   // the participant owes nothing now
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			const dropped = [];
			dispatcher.on("actionDropped", (entry) => dropped.push(entry));
			dispatcher.enqueue(readinessEvent());
			await settle();
			assert.equal(fake.starts.length, 0,
				"a stale wake was spent on a model turn");
			assert.equal(dispatcher.globalQueueDepth, 0,
				"the stale event stayed in the queue");
			assert.equal(dropped.length, 1);
			assert.equal(dropped[0].event.action.key,
				"work:7ba67cb8-W1224:4:g1");
		} finally {
			await dispatcher.stop();
		}
	});

test("the revalidation asks about the episode's own participant", async () => {
	// The read must name the participant the ACTION belongs to and use
	// the deployment's own binary and config — asking a different
	// question would answer a different question.
	//
	// Review round 1: this case used to prove that by sending an event
	// naming `baton.codex` to the tuner target and watching the read
	// follow the event. That mismatch is now refused before any read,
	// which is the correction — so the pin is on the argv of a
	// legitimate event, and the mismatch has its own case below.
	const answer = answering([]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent("work:X:1:g1", "baton.tuner"));
		await settle();
		assert.deepEqual(answer.calls[0].args,
			["--config", "/home/op/baton.json",
			 "--participant", "baton.tuner", "wait", "timeout=0"]);
		assert.equal(answer.calls[0].file, "/opt/baton/bin/baton");
	} finally {
		await dispatcher.stop();
	}
});

test("a live episode addressed to another target identity is refused",
	async () => {
		// Revalidation proves that the episode is live for baton.codex;
		// it does not make the tuner session baton.codex. The structural
		// participant must agree with the configured target identity before
		// any model turn can be spent.
		const key = "work:X:1:g1";
		const answer = answering([key]);
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent(key, "baton.codex"));
			await settle();
			assert.equal(answer.calls.length, 0,
				"a foreign-target event reached canonical revalidation");
			assert.equal(fake.starts.length, 0,
				"a live episode for baton.codex woke the baton.tuner target");
		} finally {
			await dispatcher.stop();
		}
	});

// -- what must still arrive --------------------------------------------------

test("a live episode is delivered exactly once", async () => {
	const key = "work:7ba67cb8-W1224:4:g1";
	const answer = answering([key]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent(key));
		await settle();
		assert.equal(fake.starts.length, 1, "a live wake was dropped");
		assert.match(fake.starts[0].text, /BATON READY/);
	} finally {
		await dispatcher.stop();
	}
});

test("a NEW episode for the same Work is delivered", async () => {
	// The reviewer's legitimate wake after a real implementer-to-
	// reviewer pass: same Work, later episode.
	const answer = answering(["work:7ba67cb8-W1224:6:g1"]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent("work:7ba67cb8-W1224:6:g1"));
		await settle();
		assert.equal(fake.starts.length, 1);
	} finally {
		await dispatcher.stop();
	}
});

test("an event queued behind a turn is revalidated when the target becomes idle",
	async () => {
		const answer = answering([]);
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			fake.emit("status", { threadId: "thread-a",
				status: { type: "active" } });
			dispatcher.enqueue(readinessEvent());
			await settle();
			assert.equal(answer.calls.length, 0,
				"the queued event was checked before it could drain");
			fake.emit("status", { threadId: "thread-a",
				status: { type: "idle" } });
			await settle();
			assert.equal(answer.calls.length, 1);
			assert.equal(fake.starts.length, 0,
				"the episode ended while queued but still became a turn");
		} finally {
			await dispatcher.stop();
		}
	});

test("an ordinary event is never revalidated", async () => {
	const answer = answering([]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue({ target: "tuner", source: "build",
			type: "build-failed", summary: "the build broke" });
		await settle();
		assert.equal(answer.calls.length, 0,
			"a non-readiness event was revalidated");
		assert.equal(fake.starts.length, 1);
	} finally {
		await dispatcher.stop();
	}
});

// -- a check that cannot run must not discard a wake -------------------------

test("a failed revalidation retains the event rather than dropping it",
	async () => {
		const answer = answering([], { fail: true });
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent());
			await settle();
			// retained: it became a turn rather than vanishing
			assert.equal(fake.starts.length, 1,
				"an unreachable authority silently discarded a wake");
		} finally {
			await dispatcher.stop();
		}
	});

test("a reply with no actionable set retains the event", async () => {
	const { dispatcher, fake } = bridge({
		revalidate: async () => ({ stdout: JSON.stringify({ result: {} }) }),
	});
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		assert.equal(fake.starts.length, 1);
	} finally {
		await dispatcher.stop();
	}
});

test("a deployment with no roleInstructions cannot and does not check",
	async () => {
		const fake = new FakeClient();
		const calls = [];
		const dispatcher = new EventBridge({
			config: validateConfig({
				servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
				targets: { tuner: { server: "local", threadId: "thread-a" } },
				eventSocket: "/tmp/codex-w1224-unused.sock",
				quarantineDir: freshQuarantineDir(),
			}),
			logger: quiet,
			clientFactory: () => fake,
			revalidate: async (...args) => { calls.push(args); throw new Error("x"); },
		});
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent());
			await settle();
			assert.equal(calls.length, 0);
			assert.equal(fake.starts.length, 1);
		} finally {
			await dispatcher.stop();
		}
	});

// -- the event carries the episode structurally ------------------------------

test("the producer's event names the participant and the key", () => {
	const event = readinessEvent("work:A:2:g1", "baton.claude");
	// W415 EXTENDS this block rather than relaxing it: the Work and
	// episode now ride BESIDE the key, because a consumer correlating a
	// failure with the assignment it interrupted may not parse the key
	// (docs/EFFECTIVE-BATON.md) and had no other way to learn them.
	assert.deepEqual(event.action, {
		participant: "baton.claude", key: "work:A:2:g1",
		work: "7ba67cb8-W1224", episode: 4 });
});

test("W415: an action block without the new correlation still delivers", () => {
	// A producer at an older build sends neither field. An incident with
	// no Work locator is worth less than one with it, and far more than
	// a readiness event this bridge refused to normalize.
	const bare = normalizeEvent({
		target: "baton-reviewer", source: "baton-v11",
		type: "v11-action-ready", summary: "ready",
		action: { participant: "baton.claude", key: "work:A:2:g1" } });
	assert.deepEqual(bare.action,
		{ participant: "baton.claude", key: "work:A:2:g1" });
	assert.equal(bare.action.work, undefined);
	assert.equal(bare.action.episode, undefined);
});

test("W415: a malformed correlation is refused rather than carried", () => {
	const build = (action) => () => normalizeEvent({
		target: "baton-reviewer", source: "baton-v11",
		type: "v11-action-ready", summary: "ready", action });
	assert.throws(build({ participant: "baton.claude", key: "k", episode: "4" }),
		/action.episode must be an integer episode sequence/);
	assert.throws(build({ participant: "baton.claude", key: "k", episode: 1.5 }),
		/action.episode must be an integer episode sequence/);
	assert.throws(build({ participant: "baton.claude", key: "k", work: "" }),
		/action.work/);
});

test("the dispatcher keeps the action block through normalization",
	async () => {
		const answer = answering(["work:A:2:g1"]);
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent("work:A:2:g1"));
			await settle();
			assert.equal(answer.calls.length, 1,
				"the action block did not survive normalizeEvent");
		} finally {
			await dispatcher.stop();
		}
	});

test("a malformed action block refuses the event outright", async () => {
	const { dispatcher, fake } = bridge({ revalidate: async () => ({ stdout: "{}" }) });
	try {
		await ready(dispatcher, fake);
		const answer = dispatcher.enqueue({
			...readinessEvent(), action: { participant: "", key: "" } });
		assert.equal(answer.accepted, false);
		assert.equal(answer.reason, "invalid-event");
		assert.equal(fake.starts.length, 0);
	} finally {
		await dispatcher.stop();
	}
});
