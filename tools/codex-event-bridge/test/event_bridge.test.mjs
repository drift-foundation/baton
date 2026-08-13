import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";

class FakeClient extends EventEmitter {
  constructor() {
    super();
    this.connected = true;
    this.starts = [];
    this.start = async (threadId) => ({ id: `turn-${threadId}`, status: "inProgress" });
    this.resumes = [];
  }

  async connectAndInitialize() {
    this.connected = true;
    this.emit("connected", {});
  }

  async startTurn(threadId, text, clientId) {
    this.starts.push({ threadId, text, clientId });
    return await this.start(threadId, text, clientId);
  }

  async resume(threadId) {
    this.resumes.push(threadId);
    return { thread: { id: threadId, status: { type: "idle" }, turns: [] } };
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

function config(overrides = {}) {
  return validateConfig({
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      a: { server: "local", threadId: "thread-a" },
      b: { server: "local", threadId: "thread-b" },
      c: { server: "local", threadId: "thread-c" },
    },
    eventSocket: "/tmp/codex-event-bridge-test-unused.sock",
    ...overrides,
  });
}

function bridgeWithFake(configuration = config()) {
  const fake = new FakeClient();
  const quiet = { info() {}, warn() {}, error() {}, debug() {} };
  const bridge = new EventBridge({ config: configuration, logger: quiet, clientFactory: () => fake });
  return { bridge, fake };
}

function event(target, summary = "failed") {
  return { target, source: "build", type: "build-failed", summary };
}

test("deduplicates per target", () => {
  const { bridge } = bridgeWithFake();
  assert.equal(bridge.enqueue(event("a")).accepted, true);
  assert.equal(bridge.enqueue(event("a")).reason, "duplicate");
  assert.equal(bridge.enqueue(event("b")).accepted, true);
});

test("applies per-target and global queue bounds", () => {
  const { bridge } = bridgeWithFake(config({ maxQueuePerTarget: 2, maxQueueTotal: 2 }));
  assert.equal(bridge.enqueue(event("a", "one")).accepted, true);
  assert.equal(bridge.enqueue(event("a", "two")).accepted, true);
  assert.equal(bridge.enqueue(event("a", "three")).reason, "target-queue-full");
  assert.equal(bridge.enqueue(event("b", "one")).reason, "global-queue-full");
});

test("dispatches independent idle targets concurrently", async () => {
  const { bridge, fake } = bridgeWithFake();
  const resolvers = [];
  fake.start = async (threadId) => await new Promise((resolve) => resolvers.push(() => resolve({ id: `turn-${threadId}`, status: "inProgress" })));
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  fake.emit("status", { threadId: "thread-b", status: { type: "idle" } });
  bridge.enqueue(event("a"));
  bridge.enqueue(event("b"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(fake.starts.map((start) => start.threadId).sort(), ["thread-a", "thread-b"]);
  for (const resolve of resolvers) resolve();
  await new Promise((resolve) => setImmediate(resolve));
});

test("does not dispatch an unrelated idle target", async () => {
  const { bridge, fake } = bridgeWithFake();
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  bridge.enqueue(event("b"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(fake.starts.length, 0);
});

test("reports ready only after every configured target is loaded", () => {
  const { bridge, fake } = bridgeWithFake();
  assert.equal(bridge.handleRequest({ control: "status" }).ready, false);
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  fake.emit("status", { threadId: "thread-b", status: { type: "inProgress" } });
  assert.equal(bridge.handleRequest({ control: "status" }).ready, false);
  fake.emit("status", { threadId: "thread-c", status: { type: "idle" } });
  const status = bridge.handleRequest({ control: "status" });
  assert.equal(status.ready, true);
  assert.deepEqual(status.targets.b, { connected: true, loaded: true, status: "inProgress" });
});

test("reconciles ambiguous delivery by client message id before retry", async () => {
  const { bridge, fake } = bridgeWithFake();
  let deliveredId;
  fake.start = async (_threadId, _text, clientId) => {
    deliveredId = clientId;
    throw new Error("connection dropped after send");
  };
  fake.resume = async (threadId) => ({
    thread: {
      id: threadId,
      status: { type: "idle" },
      turns: [{ id: "delivered-turn", status: "completed", items: [{ type: "userMessage", clientId: deliveredId }] }],
    },
  });
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  bridge.enqueue(event("a"));
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(fake.starts.length, 1);
  assert.equal(bridge.globalQueueDepth, 0);
});

test("initial connection resumes every configured target", async () => {
  const temporary = await import("node:fs/promises");
  const os = await import("node:os");
  const path = await import("node:path");
  const directory = await temporary.mkdtemp(path.join(os.tmpdir(), "codex-event-bridge-test-"));
  const configuration = config({ eventSocket: path.join(directory, "events.sock") });
  const { bridge, fake } = bridgeWithFake(configuration);
  try {
    await bridge.start({ listen: false });
    const deadline = Date.now() + 1000;
    while (fake.resumes.length < 3 && Date.now() < deadline) await new Promise((resolve) => setTimeout(resolve, 5));
    assert.deepEqual(fake.resumes.sort(), ["thread-a", "thread-b", "thread-c"]);
    assert.equal(bridge.statusSnapshot().ready, true);
  } finally {
    await bridge.stop();
    await temporary.rm(directory, { recursive: true });
  }
});
