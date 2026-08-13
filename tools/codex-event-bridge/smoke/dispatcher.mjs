import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import { join } from "node:path";
import { CodexClient } from "../src/codex_client.mjs";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { sendEvent } from "../src/send_event.mjs";

const endpoint = process.argv[2] ?? "ws://127.0.0.1:4500";
const directory = await mkdtemp(join(os.tmpdir(), "codex-event-dispatcher-smoke-"));
const socket = join(directory, "events.sock");
const log = { info: console.error, warn: console.error, error: console.error, debug() {} };
const tuiPeer = new CodexClient({ name: "dispatcher-smoke-tui", endpoint, logger: log });
const createdThreadIds = [];
const completed = new Map();
const messages = [];
let bridge;

tuiPeer.on("turnCompleted", ({ threadId, turn }) => {
  console.error(`[tui-peer] turn completed: ${threadId} ${turn.id} (${turn.status})`);
  completed.set(threadId, turn);
});
tuiPeer.on("itemCompleted", ({ threadId, item }) => {
  if (item.type === "agentMessage") messages.push({ threadId, text: item.text });
});
tuiPeer.on("serverRequest", (request) => console.warn(`unexpected interactive request during dispatcher smoke: ${request.method}`));

async function waitUntil(predicate, description, timeoutMs = 45_000) {
  const deadline = Date.now() + timeoutMs;
  while (!predicate()) {
    if (Date.now() >= deadline) throw new Error(`timed out waiting for ${description}`);
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
}

await tuiPeer.connectAndInitialize();
try {
  const [startedA, startedB] = await Promise.all([
    tuiPeer.request("thread/start", { cwd: process.cwd(), ephemeral: false, developerInstructions: "This thread is a protocol smoke test. Do not use tools. Answer requests concisely." }),
    tuiPeer.request("thread/start", { cwd: process.cwd(), ephemeral: false, developerInstructions: "This thread is a protocol smoke test. Do not use tools. Answer requests concisely." }),
  ]);
  createdThreadIds.push(startedA.thread.id, startedB.thread.id);
  const [seedA, seedB] = await Promise.all([
    tuiPeer.startTurn(startedA.thread.id, "Reply with exactly READY_A. Do not use tools.", "dispatcher-seed-a"),
    tuiPeer.startTurn(startedB.thread.id, "Reply with exactly READY_B. Do not use tools.", "dispatcher-seed-b"),
  ]);
  await waitUntil(() => completed.get(startedA.thread.id)?.id === seedA.id && completed.get(startedB.thread.id)?.id === seedB.id, "initial turns to materialize both rollouts");
  completed.clear();
  messages.length = 0;
  const config = validateConfig({
    servers: { local: { endpoint } },
    targets: {
      a: { server: "local", threadId: startedA.thread.id },
      b: { server: "local", threadId: startedB.thread.id },
    },
    eventSocket: socket,
  });
  bridge = new EventBridge({ config, logger: log });
  await bridge.start();
  await waitUntil(() => bridge.targetStates.get("a").status.type === "idle" && bridge.targetStates.get("b").status.type === "idle", "both dispatcher targets to resume");

  const [ackA, ackB] = await Promise.all([
    sendEvent(socket, { target: "a", source: "baton", type: "pong", summary: "PONG 2026-08-12T17:15Z — app-server bridge test marker received by baton.implementer. Acknowledge with DISPATCH_A." }),
    sendEvent(socket, { target: "b", source: "smoke", type: "external-test", summary: "Reply with exactly DISPATCH_B." }),
  ]);
  assert.equal(ackA.accepted, true);
  assert.equal(ackB.accepted, true);
  console.error(`[smoke] socket acknowledgements received: ${ackA.eventId}, ${ackB.eventId}`);
  await waitUntil(() => completed.has(startedA.thread.id) && completed.has(startedB.thread.id), "both dispatched turns to complete");
  console.error("[smoke] TUI peer observed both completions");
  await waitUntil(() => bridge.globalQueueDepth === 0 && !bridge.targetStates.get("a").activeTurn && !bridge.targetStates.get("b").activeTurn, "dispatcher to reconcile completion");
  console.error("[smoke] dispatcher reconciled both completions");

  assert.equal(completed.get(startedA.thread.id).status, "completed");
  assert.equal(completed.get(startedB.thread.id).status, "completed");
  assert.ok(messages.some((entry) => entry.threadId === startedA.thread.id && entry.text.includes("DISPATCH_A")));
  assert.ok(messages.some((entry) => entry.threadId === startedB.thread.id && entry.text.includes("DISPATCH_B")));
  assert.equal(messages.some((entry) => entry.threadId === startedA.thread.id && entry.text.includes("DISPATCH_B")), false);
  assert.equal(messages.some((entry) => entry.threadId === startedB.thread.id && entry.text.includes("DISPATCH_A")), false);
  process.stdout.write(`dispatcher smoke passed: ${startedA.thread.id}, ${startedB.thread.id}\n`);
} finally {
  await bridge?.stop();
  for (const threadId of createdThreadIds) {
    try {
      await tuiPeer.request("thread/delete", { threadId });
    } catch (error) {
      console.warn(`could not delete dispatcher smoke thread ${threadId}: ${error.message}`);
    }
  }
  tuiPeer.disconnect();
  await rm(directory, { recursive: true });
}
