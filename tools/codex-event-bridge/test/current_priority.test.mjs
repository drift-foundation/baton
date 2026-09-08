import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { EventBridge } from "../src/event_bridge.mjs";
import { validateConfig } from "../src/config.mjs";
import { actionEvent } from "../src/codex_baton_bridge.mjs";
import { inspectionRules, rulesFor } from "../src/exec_policy.mjs";

const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";
const A = "7ba67cb8-W117174";
const B = "7ba67cb8-W115599";
const quiet = { info() {}, warn() {}, error() {}, debug() {} };

function work(id, { claimed = false, episode = 1 } = {}) {
  return { kind: "work", action_key: `work:${id}:${episode}:g1`, work: id,
    local_id: id.split("-").pop(), title: id, claimed,
    phase: claimed ? "active" : "queued", episode_seq: episode, config_generation: 1 };
}

function envelope(actions) {
  return { protocol_version: 11, projection_version: "12.8", authority_uuid: UUID,
    participant: "baton.codex", snapshot_seq: 1,
    result: { timed_out: false, actionable: actions } };
}

async function settle() {
  for (let i = 0; i < 20; i++) await new Promise(resolve => setImmediate(resolve));
}

async function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), "baton-priority-"));
  const policy = join(dir, "baton.rules");
  writeFileSync(policy, [...rulesFor({ binary: "/opt/baton/bin/baton",
    config: "/home/op/baton.json", participant: "baton.codex" }),
    ...inspectionRules()].join("\n") + "\n");
  const client = new EventEmitter();
  client.connected = true;
  client.starts = [];
  client.connectAndInitialize = async () => { client.connected = true; client.emit("connected", {}); };
  client.resume = async threadId => ({ thread: { id: threadId, status: { type: "idle" }, turns: [] } });
  client.readThread = async threadId => ({ id: threadId, status: { type: "idle" }, turns: [] });
  client.startTurn = async (threadId, text, clientId) => {
    client.starts.push(clientId);
    return { id: `turn-${client.starts.length}`, status: "inProgress" };
  };
  client.disconnect = () => { const was = client.connected; client.connected = false; if (was) client.emit("disconnected"); };
  let current = [];
  let unreadable = false;
  const bridge = new EventBridge({
    config: validateConfig({
      servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
      targets: { reviewer: { server: "local", threadId: "thread-a",
        identity: { participant: "baton.codex", role: "rview", actionOwner: "baton.slaw" } } },
      roleInstructions: { binary: "/opt/baton/bin/baton", config: "/home/op/baton.json", execPolicyFile: policy },
      eventSocket: join(dir, "unused.sock"), quarantineDir: join(dir, "quarantine"),
      claimSlotRetryMs: 10, reconnectMinMs: 1, reconnectMaxMs: 2 }),
    logger: quiet, clientFactory: () => client,
    runtimeFactory: () => ({ incarnation: "test", async start() {}, async state() {},
      async incident() { return true; }, async facts() { return true; }, async end() {} }),
    revalidate: async () => {
      if (unreadable) throw new Error("authority unavailable");
      return { stdout: JSON.stringify(envelope(current)) };
    },
  });
  t.after(async () => { await bridge.stop(); rmSync(dir, { recursive: true, force: true }); });
  await bridge.start({ listen: false });
  const status = type => client.emit("status", { threadId: "thread-a", status: { type } });
  await settle();
  status("active");
  await settle();
  const event = action => actionEvent(envelope([action]), action, { target: "reviewer" });
  return { bridge, client, status, event,
    set: actions => { current = actions; }, fail: value => { unreadable = value; },
    enqueue: action => bridge.enqueue(event(action)),
    depth: () => bridge.handleRequest({ control: "status" }).targets.reviewer.queueDepth };
}

test("a downgrade while queued selects the current higher priority Work", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  // A was originally first (a blocker in the same High pool). The canonical
  // authority moves B ahead after A is downgraded; event identity is unchanged.
  f.set([a, b]);
  f.enqueue(a);
  f.enqueue(b);
  f.set([b, a]);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id]);
  assert.equal(f.depth(), 1, "the lower-ranked offer must remain queued");
  assert.equal(f.enqueue(a).reason, "in-flight", "selection must retain A's delivery identity");
  f.set([a]);
  f.client.emit("turnCompleted", { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } });
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id, f.event(a).id]);
});

test("an absent delivery does not stall the target's queued offers", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  f.set([b, a]);
  f.enqueue(a);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(a).id]);
  assert.equal(f.depth(), 0);
  f.enqueue(b);
  f.set([b]);
  f.client.emit("turnCompleted", { threadId: "thread-a", turn: { id: "turn-1", status: "completed" } });
  f.status("idle");
  await new Promise(resolve => setTimeout(resolve, 35));
  await settle();
  assert.deepEqual(f.client.starts, [f.event(a).id, f.event(b).id]);
});

test("unreadable current ordering retains both offers without a turn", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  f.set([b, a]);
  f.enqueue(a);
  f.enqueue(b);
  f.fail(true);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, []);
  assert.equal(f.depth(), 2);
  f.fail(false);
  await new Promise(resolve => setTimeout(resolve, 35));
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id]);
});

test("withdrawn higher Work does not hold a live lower offer", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  f.enqueue(b);
  f.enqueue(a);
  f.set([a]);
  f.status("idle");
  await new Promise(resolve => setTimeout(resolve, 20));
  await settle();
  assert.deepEqual(f.client.starts, [f.event(a).id]);
  assert.equal(f.depth(), 0);
});

test("a newly claimed recovery passes unclaimed higher-priority Work", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  f.enqueue(a);
  f.enqueue(b);
  f.set([a, work(B, { claimed: true })]);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id]);
  assert.equal(f.depth(), 1);
});

test("priority selection preserves a non-Work obligation at the head", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  const owed = { kind: "obligation", action_key: "obligation:7", seq: 7, work: A, flavor: "response" };
  f.enqueue(owed);
  f.enqueue(a);
  f.enqueue(b);
  f.set([owed, b, a]);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(owed).id]);
  assert.equal(f.depth(), 2);
});

test("a selected higher Work keeps its identity through an ambiguous start", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  f.enqueue(a);
  f.enqueue(b);
  f.set([b, a]);
  f.client.startTurn = async (threadId, text, clientId) => {
    f.client.starts.push(clientId);
    throw new Error("response lost after send");
  };
  f.client.resume = async threadId => ({ thread: { id: threadId,
    status: { type: "active" }, turns: [{ id: "turn-b", status: "inProgress",
      items: [{ type: "userMessage", clientId: f.event(b).id }] }] } });
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id]);
  assert.equal(f.depth(), 1, "reconciliation must remove B, not the FIFO head A");
  assert.equal(f.enqueue(a).reason, "in-flight");
});

test("an in-flight start is not preempted by newly higher Work", async t => {
  const f = await fixture(t);
  const a = work(A), b = work(B);
  let complete;
  f.client.startTurn = async (threadId, text, clientId) => {
    f.client.starts.push(clientId);
    return await new Promise(resolve => { complete = () => resolve({ id: "turn-a", status: "inProgress" }); });
  };
  f.set([a]);
  f.enqueue(a);
  f.status("idle");
  await settle();
  f.set([b, a]);
  f.enqueue(b);
  await settle();
  assert.deepEqual(f.client.starts, [f.event(a).id]);
  complete();
  await settle();
  assert.deepEqual(f.client.starts, [f.event(a).id]);
  assert.equal(f.depth(), 1);
});

test("an old episode cannot satisfy the higher Work's current delivery", async t => {
  const f = await fixture(t);
  const a = work(A), oldB = work(B), b = work(B, { episode: 2 });
  f.enqueue(a);
  f.enqueue(oldB);
  f.enqueue(b);
  f.set([b, a]);
  f.status("idle");
  await settle();
  assert.deepEqual(f.client.starts, [f.event(b).id]);
  assert.equal(f.depth(), 2, "old episode and lower offer must not be confused with the selected delivery");
});
