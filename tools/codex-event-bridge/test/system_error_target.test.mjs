// W43539: `systemError` is a failed configured Codex context, not an idle
// target. Readiness stays retained until the managed lifecycle mints and
// renders a fresh thread.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { actionEvent } from "../src/codex_baton_bridge.mjs";
import { inspectionRules, rulesFor } from "../src/exec_policy.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";

const quiet = { info() {}, warn() {}, error() {}, debug() {} };
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";
const WORK = "7ba67cb8-W43539";
const EPISODE = 43539;
const KEY = `work:${WORK}:${EPISODE}:g1`;
const FIXTURE_POLICY = join(mkdtempSync("/tmp/w43539-fixture-policy-"),
  "baton.rules");
writeFileSync(FIXTURE_POLICY,
  rulesFor({ binary: "/opt/baton/bin/baton", config: "/home/op/baton.json",
    participant: "baton.codex" }).concat(inspectionRules()).join("\n") + "\n");

class FakeClient extends EventEmitter {
  constructor(threadId) {
    super();
    this.threadId = threadId;
    this.connected = true;
    this.starts = [];
    this.resumeStatus = { type: "idle" };
    this.resumeTurns = [];
    this.readStatus = { type: "idle" };
    this.readTurns = [];
  }

  async connectAndInitialize() {
    this.connected = true;
    this.emit("connected", {});
  }

  async resume(threadId) {
    return { thread: { id: threadId, status: this.resumeStatus,
      turns: this.resumeTurns } };
  }

  async readThread(threadId) {
    return { id: threadId, status: this.readStatus, turns: this.readTurns };
  }

  async startTurn(threadId, text, clientId) {
    const turn = { id: `turn-${this.starts.length + 1}`, status: "inProgress" };
    this.starts.push({ threadId, text, clientId, turn });
    return turn;
  }

  disconnect() {
    const wasConnected = this.connected;
    this.connected = false;
    if (wasConnected) this.emit("disconnected");
  }
}

function config(threadId) {
  return validateConfig({
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      codex: { server: "local", threadId,
        identity: { participant: "baton.codex", role: "rview",
          actionOwner: "baton.slaw" } },
    },
    roleInstructions: { binary: "/opt/baton/bin/baton",
      config: "/home/op/baton.json", execPolicyFile: FIXTURE_POLICY },
    eventSocket: "/tmp/codex-w43539-unused.sock",
    quarantineDir: freshQuarantineDir(),
    reconnectMinMs: 1,
    reconnectMaxMs: 2,
  });
}

function canonical(actionable) {
  return { protocol_version: 11, projection_version: "12.7",
    authority_uuid: UUID, participant: "baton.codex", snapshot_seq: 1,
    result: { timed_out: false, actionable } };
}

function entry(work = WORK, episode = EPISODE, claimed = false) {
  return { kind: "work", action_key: `work:${work}:${episode}:g1`, work,
    episode_seq: episode, config_generation: 1, claimed };
}

function readinessEvent({ work = WORK, episode = EPISODE } = {}) {
  const action = entry(work, episode, false);
  return actionEvent({ authority_uuid: UUID, participant: "baton.codex",
    result: { actionable: [] } }, { ...action,
    local_id: work.split("-").pop(), title: "recover terminal context",
    phase: "queued" }, { target: "codex" });
}

function bridge({ threadId = "thread-a", actionable = [entry()] } = {}) {
  const fake = new FakeClient(threadId);
  const published = [];
  let reads = 0;
  const dispatcher = new EventBridge({
    config: config(threadId), logger: quiet,
    clientFactory: () => fake,
    runtimeFactory: () => ({
      incarnation: "run-1",
      async start() {},
      async state(name, detail) { published.push([name, detail]); },
      async incident() { return true; },
      async facts() { return true; },
      async end() {},
    }),
    revalidate: async () => {
      reads += 1;
      return { stdout: JSON.stringify(canonical(actionable)) };
    },
  });
  return { dispatcher, fake, published, reads: () => reads };
}

async function settle(times = 10) {
  for (let index = 0; index < times; index += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
}

async function start(rig) {
  await rig.dispatcher.start({ listen: false });
  await settle();
}

async function finish(rig, status) {
  rig.fake.emit("turnCompleted", { threadId: rig.fake.threadId,
    turn: { id: rig.fake.starts.at(-1).turn.id, status } });
  await settle();
}

test("failed/systemError publishes failed and retains queued readiness", async () => {
  const rig = bridge();
  rig.fake.readStatus = { type: "systemError" };
  rig.fake.readTurns = [{ id: "turn-1", status: "failed" }];
  try {
    await start(rig);
    rig.dispatcher.enqueue(readinessEvent());
    await settle();
    await finish(rig, "failed");

    assert.equal(rig.published.some(([state]) => state === "idle"), false,
      "the terminal context was published idle before its status was read");
    const failed = rig.published.findLast(([state]) => state === "failed");
    assert.ok(failed);
    assert.equal(failed[1].cause, "internal");
    assert.equal(failed[1].session, "thread-a");
    assert.match(failed[1].detail, /baton\.codex/);
    assert.match(failed[1].detail, /systemError/);
    assert.match(failed[1].detail, /failed turn turn-1/);

    const queued = readinessEvent({ work: "7ba67cb8-W43540", episode: 43540 });
    assert.equal(rig.dispatcher.enqueue(queued).accepted, true);
    await settle();
    assert.equal(rig.dispatcher.enqueue(queued).reason, "in-flight");
    assert.equal(rig.fake.starts.length, 1,
      "readiness drained into a systemError context");
    assert.equal(rig.dispatcher.globalQueueDepth, 1);

    const row = rig.dispatcher.statusSnapshot();
    assert.equal(row.ready, false);
    assert.equal(row.targets.codex.deliverable, false);
    assert.deepEqual({ participant: row.targets.codex.terminalFailure.participant,
      session: row.targets.codex.terminalFailure.session,
      failedTurnId: row.targets.codex.terminalFailure.failedTurnId,
      status: row.targets.codex.terminalFailure.status,
      queuedActionCount: row.targets.codex.terminalFailure.queuedActionCount },
      { participant: "baton.codex", session: "thread-a",
        failedTurnId: "turn-1", status: "systemError", queuedActionCount: 1 });

    rig.fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
    await settle();
    assert.equal(rig.dispatcher.statusSnapshot().targets.codex.deliverable, false,
      "a later idle notification cleared a sticky terminal failure");
    assert.equal(rig.published.at(-1)[0], "failed");

    const failureReports = rig.published.filter(([state]) => state === "failed").length;
    rig.fake.emit("turnCompleted", { threadId: "thread-a",
      turn: { id: "turn-1", status: "failed" } });
    await settle();
    assert.equal(rig.published.filter(([state]) => state === "failed").length,
      failureReports, "a duplicate completion republished the same failure");
    assert.equal(rig.fake.starts.length, 1,
      "a duplicate completion drained retained readiness");
  } finally {
    await rig.dispatcher.stop();
  }
});

test("failed/idle is reusable and drains the next action", async () => {
  const rig = bridge({ actionable: [entry(),
    entry("7ba67cb8-W43540", 43540)] });
  try {
    await start(rig);
    rig.dispatcher.enqueue(readinessEvent());
    await settle();
    await finish(rig, "failed");
    assert.equal(rig.published.at(-1)[0], "idle");
    assert.equal(rig.dispatcher.statusSnapshot().targets.codex.deliverable, true);

    rig.dispatcher.enqueue(readinessEvent({ work: "7ba67cb8-W43540",
      episode: 43540 }));
    await settle();
    assert.equal(rig.fake.starts.length, 2);
  } finally {
    await rig.dispatcher.stop();
  }
});

test("completed/idle stays healthy and skips failed-turn settlement", async () => {
  const rig = bridge();
  try {
    await start(rig);
    rig.dispatcher.enqueue(readinessEvent());
    await settle();
    const before = rig.reads();
    await finish(rig, "completed");
    assert.equal(rig.reads(), before,
      "a successful completion performed failed-turn claim reconciliation");
    assert.equal(rig.published.at(-1)[0], "idle");
    assert.equal(rig.dispatcher.statusSnapshot().ready, true);
  } finally {
    await rig.dispatcher.stop();
  }
});

test("reconnect restores systemError as failed and never calls it healthy", async () => {
  const rig = bridge();
  rig.fake.resumeStatus = { type: "systemError" };
  rig.fake.resumeTurns = [{ id: "turn-reconnect", status: "failed" }];
  try {
    await start(rig);
    const row = rig.dispatcher.statusSnapshot();
    assert.equal(row.ready, false);
    assert.equal(row.targets.codex.terminalFailure.failedTurnId,
      "turn-reconnect");
    assert.equal(rig.published.at(-1)[0], "failed");
  } finally {
    await rig.dispatcher.stop();
  }
});

test("a managed restart with a fresh thread drains the retained offer once",
  async () => {
    const failed = bridge({ threadId: "thread-failed" });
    failed.fake.resumeStatus = { type: "systemError" };
    try {
      await start(failed);
      failed.dispatcher.enqueue(readinessEvent());
      await settle();
      assert.equal(failed.fake.starts.length, 0);
    } finally {
      await failed.dispatcher.stop();
    }

    const fresh = bridge({ threadId: "thread-fresh" });
    try {
      await start(fresh);
      assert.equal(fresh.dispatcher.statusSnapshot().ready, true);
      assert.equal(fresh.dispatcher.enqueue(readinessEvent()).accepted, true);
      await settle();
      assert.equal(fresh.fake.starts.length, 1);
      assert.equal(fresh.fake.starts[0].threadId, "thread-fresh");
      assert.equal(fresh.dispatcher.globalQueueDepth, 0);
    } finally {
      await fresh.dispatcher.stop();
    }
  });
