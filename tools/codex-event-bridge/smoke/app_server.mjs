// Manual installed-server test; excluded from the default unit suite.
import assert from "node:assert/strict";
import { CodexClient } from "../src/codex_client.mjs";

const endpoint = process.argv[2] ?? "ws://127.0.0.1:4500";
const quiet = { info() {}, warn: console.warn, error: console.error, debug() {} };
const tuiPeer = new CodexClient({ name: "smoke-tui-peer", endpoint, logger: quiet });
const bridgePeer = new CodexClient({ name: "smoke-bridge-peer", endpoint, logger: quiet });
const completed = new Map();
const peerStarts = [];
const peerMessages = [];
const createdThreadIds = [];

tuiPeer.on("turnStarted", ({ threadId, turn }) => peerStarts.push({ threadId, turnId: turn.id }));
tuiPeer.on("turnCompleted", ({ threadId, turn }) => completed.set(turn.id, { threadId, turn }));
tuiPeer.on("itemCompleted", ({ threadId, item }) => {
  if (item.type === "agentMessage") peerMessages.push({ threadId, text: item.text });
});
for (const client of [tuiPeer, bridgePeer]) {
  client.on("serverRequest", (request) => console.warn(`unexpected interactive request during smoke test: ${request.method}`));
}

async function waitForCompletion(turnId, timeoutMs = 120_000) {
  const deadline = Date.now() + timeoutMs;
  while (!completed.has(turnId)) {
    if (Date.now() >= deadline) throw new Error(`timed out waiting for ${turnId}`);
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  return completed.get(turnId);
}

async function createSeededThread(marker) {
  const response = await tuiPeer.request("thread/start", { cwd: process.cwd(), ephemeral: false });
  createdThreadIds.push(response.thread.id);
  const turn = await tuiPeer.startTurn(response.thread.id, `Remember ${marker}. Reply with exactly READY_${marker}. Do not use tools.`, `seed-${marker}`);
  const completedTurn = await waitForCompletion(turn.id);
  assert.equal(completedTurn.turn.status, "completed");
  return response;
}

await tuiPeer.connectAndInitialize();
await bridgePeer.connectAndInitialize();
try {
  const [startedA, startedB] = await Promise.all([createSeededThread("MARKER_A"), createSeededThread("MARKER_B")]);
  const threadA = startedA.thread.id;
  const threadB = startedB.thread.id;
  const [resumedA, resumedB] = await Promise.all([bridgePeer.resume(threadA), bridgePeer.resume(threadB)]);
  for (const [started, resumed] of [[startedA, resumedA], [startedB, resumedB]]) {
    assert.equal(resumed.model, started.model);
    assert.equal(resumed.cwd, started.cwd);
    assert.deepEqual(resumed.instructionSources, started.instructionSources);
    assert.deepEqual(resumed.sandbox, started.sandbox);
    assert.equal(resumed.approvalPolicy, started.approvalPolicy);
    assert.equal(resumed.approvalsReviewer, started.approvalsReviewer);
  }

  const [turnA, turnB] = await Promise.all([
    bridgePeer.startTurn(threadA, "What marker did I ask you to remember? Reply with only the marker. Do not use tools.", "smoke-a"),
    bridgePeer.startTurn(threadB, "What marker did I ask you to remember? Reply with only the marker. Do not use tools.", "smoke-b"),
  ]);
  const [doneA, doneB] = await Promise.all([waitForCompletion(turnA.id), waitForCompletion(turnB.id)]);

  assert.equal(doneA.threadId, threadA);
  assert.equal(doneB.threadId, threadB);
  assert.equal(doneA.turn.status, "completed");
  assert.equal(doneB.turn.status, "completed");
  assert.ok(peerStarts.some((entry) => entry.threadId === threadA && entry.turnId === turnA.id));
  assert.ok(peerStarts.some((entry) => entry.threadId === threadB && entry.turnId === turnB.id));
  assert.ok(peerMessages.some((entry) => entry.threadId === threadA && entry.text.includes("MARKER_A")));
  assert.ok(peerMessages.some((entry) => entry.threadId === threadB && entry.text.includes("MARKER_B")));
  assert.equal(peerMessages.some((entry) => entry.threadId === threadA && entry.text.includes("MARKER_B")), false);
  assert.equal(peerMessages.some((entry) => entry.threadId === threadB && entry.text.includes("MARKER_A")), false);
  process.stdout.write(`app-server smoke passed: ${threadA}, ${threadB}\n`);
} finally {
  bridgePeer.disconnect();
  for (const threadId of createdThreadIds) {
    try {
      await tuiPeer.request("thread/delete", { threadId });
    } catch (error) {
      console.warn(`could not delete smoke-test thread ${threadId}: ${error.message}`);
    }
  }
  tuiPeer.disconnect();
}
