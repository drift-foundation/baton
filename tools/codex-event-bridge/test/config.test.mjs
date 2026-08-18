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

// W4 (finding-v10-runtime-removal): the `baton` block and the
// per-target `participant` were the ALL-SESSION STACK's configuration —
// consumed only by the retired `stack.mjs`, which spawned one v10
// monitor per participant. The generic dispatcher never read them, so
// they left with the stack rather than being kept as dead schema.
test("the retired stack-only configuration is gone", () => {
  const raw = base();
  raw.baton = { binary: "/opt/baton/bin/baton", config: "/srv/x.json" };
  raw.targets.a.participant = "baton.reviewer";
  const config = validateConfig(raw);
  assert.equal(config.baton, undefined,
               "the stack's baton block is still validated");
  assert.equal(config.targets.a.participant, undefined,
               "the stack's per-target participant is still validated");
  // ...and the generic transport it shared a file with is untouched.
  assert.ok(config.targets.a.server);
  assert.ok(config.eventSocket);
});
