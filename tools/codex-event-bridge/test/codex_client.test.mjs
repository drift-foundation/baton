import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { CodexClient } from "../src/codex_client.mjs";

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
      else if (message.method === "thread/resume") this.receive({ id: message.id, result: { thread: { id: message.params.threadId, status: { type: "idle" }, turns: [] } } });
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
