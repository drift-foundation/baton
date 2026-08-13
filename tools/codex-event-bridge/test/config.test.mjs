import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";

function base() {
  return {
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      a: { server: "local", threadId: "thread-a" },
      b: { server: "local", threadId: "thread-b" },
    },
  };
}

test("validates named servers and isolated targets", () => {
  const config = validateConfig(base());
  assert.equal(config.targets.a.threadId, "thread-a");
  assert.equal(config.maxQueuePerTarget, 100);
  assert.equal(config.maxQueueTotal, 1000);
});

test("rejects a non-loopback app-server", () => {
  const raw = base();
  raw.servers.local.endpoint = "ws://0.0.0.0:4500";
  assert.throws(() => validateConfig(raw), /must be loopback/);
});

test("rejects duplicate target assignments", () => {
  const raw = base();
  raw.targets.b.threadId = "thread-a";
  assert.throws(() => validateConfig(raw), /assigned to more than one target/);
});

test("requires global capacity to cover one target", () => {
  const raw = base();
  raw.maxQueuePerTarget = 10;
  raw.maxQueueTotal = 5;
  assert.throws(() => validateConfig(raw), /maxQueueTotal/);
});

test("validates Baton assignments for independently routed sessions", () => {
  const raw = base();
  raw.baton = {
    binary: "/opt/baton/bin/baton",
    config: "/srv/mailbox/baton.json",
  };
  raw.targets.a.participant = "baton.reviewer";
  raw.targets.b.participant = "lang.reviewer";
  const config = validateConfig(raw);
  assert.equal(config.baton.waitTimeoutSeconds, 60);
  assert.equal(config.targets.a.participant, "baton.reviewer");
  assert.equal(config.targets.b.participant, "lang.reviewer");
});

test("rejects one Baton participant assigned to two Codex sessions", () => {
  const raw = base();
  raw.targets.a.participant = "baton.reviewer";
  raw.targets.b.participant = "baton.reviewer";
  assert.throws(() => validateConfig(raw), /participant baton\.reviewer is assigned to more than one target/);
});

test("requires absolute Baton paths", () => {
  const raw = base();
  raw.baton = { binary: "bin/baton", config: "/srv/mailbox/baton.json" };
  assert.throws(() => validateConfig(raw), /baton\.binary must be an absolute path/);
});
