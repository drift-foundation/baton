import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { CodexClient } from "../src/codex_client.mjs";

// W415: the dispatcher refuses to start unless the deployment-owned
// execpolicy file authorizes each managed participant's canonical Baton
// operations. These fixtures therefore need a real one.
import { mkdtempSync as _mkdtemp, writeFileSync as _write } from "node:fs";
import { join as _join } from "node:path";
import { inspectionRules as _inspectionRules,
         rulesFor as _rulesFor } from "../src/exec_policy.mjs";
const _policyDir = _mkdtemp("/tmp/w415-fixture-policy-");
export const FIXTURE_POLICY = _join(_policyDir, "baton.rules");
// W2845: and the deployment-wide read-only Docker inspection profile,
// which `start()` preflights on the same nominated file.
_write(FIXTURE_POLICY, ["/srv/baton/baton.json", "/home/op/baton.json"]
	.flatMap((config) => ["baton.tuner", "baton.codex", "a.b"]
		.flatMap((participant) => _rulesFor({
			binary: "/opt/baton/bin/baton", config, participant })))
	.concat(_inspectionRules())
	.join("\n") + "\n");


class FakeWebSocket {
  static instances = [];

  constructor(endpoint) {
    this.endpoint = endpoint;
    this.readyState = 0;
    this.events = new EventEmitter();
    this.sent = [];
    FakeWebSocket.instances.push(this);
    queueMicrotask(() => {
      this.readyState = 1;
      this.events.emit("open", {});
    });
  }

  addEventListener(name, listener) {
    this.events.on(name, listener);
  }

  removeEventListener(name, listener) {
    this.events.off(name, listener);
  }

  send(text) {
    const message = JSON.parse(text);
    this.sent.push(message);
    queueMicrotask(() => {
      if (message.method === "initialize") this.receive({ id: message.id, result: { userAgent: "fake" } });
      else if (message.method === "thread/start") this.receive({ id: message.id, result: { sandbox: { type: "workspaceWrite", execPolicyFile: FIXTURE_POLICY }, thread: { id: "thread-new", status: { type: "idle" }, turns: [] } } });
      else if (message.method === "thread/resume") this.receive({ id: message.id, result: { sandbox: { type: "workspaceWrite", execPolicyFile: FIXTURE_POLICY }, thread: { id: message.params.threadId, status: { type: "idle" }, turns: [] } } });
      else if (message.method === "turn/start") this.receive({ id: message.id, result: { turn: { id: `turn-${message.params.threadId}`, status: "inProgress" } } });
    });
  }

  receive(message) {
    this.events.emit("message", { data: JSON.stringify(message) });
  }

  close() {
    this.readyState = 3;
    this.events.emit("close", {});
  }
}

test("one initialized connection resumes and addresses multiple threads", async () => {
  FakeWebSocket.instances = [];
  const client = new CodexClient({ name: "local", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
  await client.connectAndInitialize();
  await client.resume("thread-a");
  await client.resume("thread-b");
  await client.startTurn("thread-b", "hello", "event-123");

  const sent = FakeWebSocket.instances[0].sent;
  assert.equal(sent[0].method, "initialize");
  assert.equal(sent[1].method, "initialized");
  assert.equal(Object.hasOwn(sent[1], "params"), false);
  assert.deepEqual(sent.filter((message) => message.method === "thread/resume").map((message) => message.params.threadId), ["thread-a", "thread-b"]);
  const start = sent.find((message) => message.method === "turn/start");
  assert.equal(start.params.threadId, "thread-b");
  assert.equal(start.params.clientUserMessageId, "event-123");
  assert.deepEqual(start.params.input, [{ type: "text", text: "hello", text_elements: [] }]);
  client.disconnect();
});

test("routes status notifications by thread id", async () => {
  FakeWebSocket.instances = [];
  const client = new CodexClient({ name: "local", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
  await client.connectAndInitialize();
  const statuses = [];
  client.on("status", (event) => statuses.push(event));
  FakeWebSocket.instances[0].receive({ method: "thread/status/changed", params: { threadId: "thread-a", status: { type: "active", activeFlags: [] } } });
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(client.statusOf("thread-a").type, "active");
  assert.equal(statuses.at(-1).threadId, "thread-a");
  client.disconnect();
});

test("creates and resumes threads with configured developer instructions", async () => {
  FakeWebSocket.instances = [];
  const client = new CodexClient({ name: "local", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
  await client.connectAndInitialize();
  const started = await client.startThread({ cwd: "/work", developerInstructions: "Tune packaging only." });
  await client.resume(started.thread.id, { developerInstructions: "Tune packaging only." });
  const sent = FakeWebSocket.instances[0].sent;
  const start = sent.find((message) => message.method === "thread/start");
  const resume = sent.find((message) => message.method === "thread/resume");
  // W415: the exact operands are still pinned, and now include the
  // non-interactive approval policy on BOTH paths. This assertion was
  // extended rather than relaxed — the dispatcher declaring the policy
  // is the behaviour change this Work makes.
  // W415: a caller that declares no writable root sends no sandbox
  // operands at all, so an ordinary thread is untouched by this.
  assert.deepEqual(start.params, { cwd: "/work", developerInstructions: "Tune packaging only." });
  assert.deepEqual(resume.params, { threadId: "thread-new", developerInstructions: "Tune packaging only." });
  client.disconnect();
});

// -- W484: a completion that arrives before its waiter -----------------------
//
// `work/records/2026/08/finding-codex-turn-completion-race/`. Every
// production caller installs its wait AFTER awaiting `turn/start`. A
// `turn/completed` delivered before that continuation runs was emitted
// to nobody, and the wait — with no prior-state check and no timeout —
// never settled. W424 added a second operator-visible caller of the
// pattern, in a command where a hang is indistinguishable from a slow
// model.

class RacingWebSocket extends FakeWebSocket {
	/** Completes the turn BEFORE resolving `turn/start`, which is the
	 *  ordering the waiter cannot survive without retention. */
	send(text) {
		const message = JSON.parse(text);
		this.sent.push(message);
		queueMicrotask(() => {
			if (message.method === "initialize") {
				this.receive({ id: message.id, result: { userAgent: "fake" } });
			} else if (message.method === "thread/resume") {
				this.receive({ id: message.id, result: { sandbox: { type: "workspaceWrite", execPolicyFile: FIXTURE_POLICY }, thread: { id: message.params.threadId, status: { type: "idle" }, turns: [] } } });
			} else if (message.method === "turn/start") {
				const turn = { id: `turn-${message.params.threadId}`, status: "inProgress" };
				this.receive({ method: "turn/completed",
					params: { threadId: message.params.threadId,
						turn: { ...turn, status: "completed" } } });
				this.receive({ id: message.id, result: { turn } });
			}
		});
	}
}

test("a completion that arrives before the waiter still resolves it", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "race", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: RacingWebSocket });
	await client.connectAndInitialize();
	await client.resume("thread-a");
	const turn = await client.startTurn("thread-a", "hello", "event-1");
	// Raced against a timer ON PURPOSE. The defect's symptom is a wait
	// that never settles, and a regression whose failure mode is a
	// hanging suite is not a regression anybody can read — so the
	// unsettled case FAILS here instead of stopping the run.
	const settled = await Promise.race([
		client.waitForTurnCompletion("thread-a", turn.id),
		new Promise((resolve) => setTimeout(() => resolve("never settled"), 250)),
	]);
	assert.notEqual(settled, "never settled",
		"the completion arrived before the waiter and was discarded");
	assert.equal(settled.id, turn.id);
	assert.equal(settled.status, "completed");
});

test("a completion that arrives after the waiter behaves as before", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "ordered", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	await client.resume("thread-a");
	const turn = await client.startTurn("thread-a", "hello", "event-1");
	const waiting = client.waitForTurnCompletion("thread-a", turn.id);
	FakeWebSocket.instances[0].receive({ method: "turn/completed",
		params: { threadId: "thread-a", turn: { id: turn.id, status: "completed" } } });
	assert.equal((await waiting).status, "completed");
	// and nothing is left behind for a later wait to find
	assert.equal(client.takeCompletion("thread-a", turn.id), null);
});

test("thread and turn identity both have to match", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "identity", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	const socket = FakeWebSocket.instances[0];
	socket.receive({ method: "turn/completed",
		params: { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } } });
	assert.equal(client.takeCompletion("thread-b", "turn-1"), null,
		"another thread's completion satisfied this waiter");
	assert.equal(client.takeCompletion("thread-a", "turn-2"), null,
		"another turn's completion satisfied this waiter");
	assert.equal(client.takeCompletion("thread-a", "turn-1").status, "completed");
});

test("one completion answers one wait", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "once", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	FakeWebSocket.instances[0].receive({ method: "turn/completed",
		params: { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } } });
	// Timer-raced for the same reason as the case above: an unsettled
	// wait must fail this file, not stall it.
	const settled = await Promise.race([
		client.waitForTurnCompletion("thread-a", "turn-1"),
		new Promise((resolve) => setTimeout(() => resolve("never settled"), 250)),
	]);
	assert.notEqual(settled, "never settled");
	assert.equal(settled.id, "turn-1");
	assert.equal(client.takeCompletion("thread-a", "turn-1"), null,
		"the record survived being consumed");
});

test("a duplicate completion does not accumulate", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "dupe", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	for (let index = 0; index < 5; index += 1) {
		FakeWebSocket.instances[0].receive({ method: "turn/completed",
			params: { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } } });
	}
	assert.equal(client.completions.size, 1);
	assert.ok(client.takeCompletion("thread-a", "turn-1"));
	assert.equal(client.takeCompletion("thread-a", "turn-1"), null);
});

test("retention is bounded and evicts the oldest unconsumed record", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "bounded", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket, maxRetainedCompletions: 3 });
	await client.connectAndInitialize();
	for (const id of ["t1", "t2", "t3", "t4"]) {
		FakeWebSocket.instances[0].receive({ method: "turn/completed",
			params: { threadId: "thread-a", turn: { id, status: "completed" } } });
	}
	assert.equal(client.completions.size, 3);
	assert.equal(client.takeCompletion("thread-a", "t1"), null,
		"the oldest record was not the one evicted");
	for (const id of ["t2", "t3", "t4"]) {
		assert.ok(client.takeCompletion("thread-a", id), id);
	}
});

test("a disconnect drops retained completions and fails waits closed",
	async () => {
		FakeWebSocket.instances = [];
		const client = new CodexClient({ name: "closed", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
		await client.connectAndInitialize();
		FakeWebSocket.instances[0].receive({ method: "turn/completed",
			params: { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } } });
		const pending = client.waitForTurnCompletion("thread-a", "turn-2");
		client.disconnect();
		await assert.rejects(pending, /disconnected/);
		assert.equal(client.completions.size, 0);
		assert.equal(client.takeCompletion("thread-a", "turn-1"), null,
			"a pre-disconnect completion survived the disconnect");
	});

test("a waiter installed just after disconnect also fails closed", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "closed-before-wait", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	client.disconnect();
	let settled = false;
	const pending = client.waitForTurnCompletion("thread-a", "turn-1")
		.then((value) => { settled = true; return { value }; },
			(error) => { settled = true; return { error }; });
	await new Promise((resolve) => setTimeout(resolve, 25));
	const settledBeforeCleanup = settled;
	if (!settled) {
		client.emit("disconnected");
	}
	const result = await pending;
	assert.equal(settledBeforeCleanup, true,
		"the waiter missed the earlier disconnect and hung");
	assert.ok(result.error instanceof Error, result);
});

test("a completion with no turn id is not retained", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "malformed", endpoint: "ws://127.0.0.1:4500", WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	FakeWebSocket.instances[0].receive({ method: "turn/completed",
		params: { threadId: "thread-a" } });
	assert.equal(client.completions.size, 0);
});

// -- W415: the managed thread declares NO overrides ----------------------
//
// Three shapes were rejected before this one: an approval policy, a
// writable coordination-home root, and a narrowed version of that root.
// The approver then ruled out arbitrary per-thread overrides entirely.
// The capability now comes from a deployment-owned execpolicy file, so
// what this client must do is send NOTHING extra.

test("W415: neither thread path sends a sandbox or approval override", async () => {
	FakeWebSocket.instances = [];
	const client = new CodexClient({ name: "local", endpoint: "ws://127.0.0.1:4500",
		WebSocketImpl: FakeWebSocket });
	await client.connectAndInitialize();
	const started = await client.startThread({ cwd: "/work",
		developerInstructions: "review" });
	await client.resume(started.thread.id, { developerInstructions: "review" });
	const sent = FakeWebSocket.instances[0].sent;
	for (const method of ["thread/start", "thread/resume"]) {
		const message = sent.find((entry) => entry.method === method);
		for (const forbidden of ["sandbox", "config", "approvalPolicy"]) {
			assert.equal(message.params[forbidden], undefined,
				`${method} must not send ${forbidden}`);
		}
	}
	client.disconnect();
});
