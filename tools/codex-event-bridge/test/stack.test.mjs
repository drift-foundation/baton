import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";
import { buildStackPlan } from "../src/stack.mjs";

function stackConfig() {
  return validateConfig({
    baton: {
      binary: "/opt/baton/bin/baton",
      config: "/srv/mailbox/baton.json",
      waitTimeoutSeconds: 30,
      retryMs: 250,
    },
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      baton: { server: "local", threadId: "thread-baton", participant: "baton.reviewer" },
      lang: { server: "local", threadId: "thread-lang", participant: "lang.reviewer" },
    },
    eventSocket: "/run/user/1000/codex-events.sock",
  });
}

test("plans one Baton poller for each mapped Codex session", () => {
  const plan = buildStackPlan(stackConfig());
  assert.deepEqual(plan.servers, [{ name: "local", endpoint: "ws://127.0.0.1:4500" }]);
  assert.deepEqual(plan.monitors, [
    { target: "baton", participant: "baton.reviewer" },
    { target: "lang", participant: "lang.reviewer" },
  ]);
});

test("complete stack requires Baton deployment configuration", () => {
  const config = stackConfig();
  assert.throws(() => buildStackPlan({ ...config, baton: null }), /requires baton\.binary and baton\.config/);
});

test("complete stack requires a participant for every target", () => {
  const config = stackConfig();
  const targets = { ...config.targets, lang: { ...config.targets.lang, participant: null } };
  assert.throws(() => buildStackPlan({ ...config, targets }), /target lang requires participant/);
});
