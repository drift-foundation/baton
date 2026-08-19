import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { resolveTargetInstructions } from "../src/main.mjs";
import { readRoleInstructions, validateRoleInstructions } from "../src/role_instructions.mjs";

const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

function envelope({ participant = "baton.tuner", role = "tuner", instructions = "Tune packaging only." } = {}) {
  return {
    protocol_version: 11,
    projection_version: "9.2",
    participant,
    authority_uuid: UUID,
    snapshot_seq: 42,
    result: { participant, role, instructions, configuration_generation: 3 },
  };
}

function rawConfig() {
  return {
    roleInstructions: { binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json" },
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      tuner: { server: "local", threadId: "thread-tuner", identity: { participant: "baton.tuner", role: "tuner" } },
    },
    eventSocket: "/tmp/codex-role-instructions-test.sock",
  };
}

test("the role-instruction CLI invocation uses explicit launcher context and role", async () => {
  let observed;
  const resolved = await readRoleInstructions(
    { binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json" },
    { participant: "baton.tuner", role: "tuner" },
    { execute: async (file, argv) => {
      observed = { file, argv };
      return { stdout: JSON.stringify(envelope()) };
    } });
  assert.deepEqual(observed, {
    file: "/opt/baton/bin/baton",
    argv: ["--config", "/srv/baton/baton.json", "--participant", "baton.tuner", "instructions", "role=tuner"],
  });
  assert.equal(resolved.instructions, "Tune packaging only.");
  assert.equal(resolved.configurationGeneration, 3);
});

test("instruction envelopes fail closed on participant, role, text, generation, and projection", () => {
  const identity = { participant: "baton.tuner", role: "tuner" };
  for (const [change, pattern] of [
    [(payload) => { payload.participant = "baton.codex"; }, /participant/],
    [(payload) => { payload.result.role = "review"; }, /selected role/],
    [(payload) => { payload.result.instructions = ""; }, /non-empty instructions/],
    [(payload) => { payload.result.configuration_generation = 0; }, /positive configuration_generation/],
    [(payload) => { payload.projection_version = "8.9"; }, /role-instruction contract/],
    // W5: projection 12 is SUPPORTED — the major moved for the poke
    // action kind, and the role-instruction result itself did not
    // change, so this consumer widened in the same candidate.
    [(payload) => { payload.projection_version = "13.0"; }, /role-instruction contract/],
  ]) {
    const payload = envelope();
    change(payload);
    assert.throws(() => validateRoleInstructions(payload, identity), pattern);
  }
});

test("instruction envelopes accept the bounded projection-9/10 contract", () => {
  const identity = { participant: "baton.tuner", role: "tuner" };
  for (const projection of ["9.0", "9.9", "10.0", "10.4"]) {
    const payload = envelope();
    payload.projection_version = projection;
    assert.equal(validateRoleInstructions(payload, identity).role, "tuner");
  }
});

test("Codex target configuration requires an explicit source and identity as a pair", () => {
  const config = validateConfig(rawConfig());
  assert.equal(config.targets.tuner.identity.participant, "baton.tuner");
  assert.equal(config.roleInstructions.binary, "/opt/baton/bin/baton");
  const noSource = rawConfig();
  delete noSource.roleInstructions;
  assert.throws(() => validateConfig(noSource), /identities require roleInstructions/);
  const noIdentity = rawConfig();
  delete noIdentity.targets.tuner.identity;
  assert.throws(() => validateConfig(noIdentity), /requires an identity/);
});

test("Codex targets cannot assign one Baton participant to distinct threads", () => {
  const raw = rawConfig();
  raw.targets.reviewer = {
    server: "local",
    threadId: "thread-reviewer",
    identity: { participant: "baton.tuner", role: "review" },
  };
  assert.throws(() => validateConfig(raw), /participant baton\.tuner is assigned to more than one target/);
});

test("every configured Codex resume receives the accepted developer instructions", async () => {
  const config = validateConfig(rawConfig());
  const resolved = await resolveTargetInstructions(config, {
    read: async (_source, identity) => ({ ...identity, instructions: "Tune packaging only.", configurationGeneration: 3 }),
  });
  class FakeClient extends EventEmitter {
    constructor() { super(); this.connected = true; this.resumes = []; }
    async connectAndInitialize() { this.connected = true; this.emit("connected", {}); }
    async resume(threadId, options) {
      this.resumes.push({ threadId, options });
      return { thread: { id: threadId, status: { type: "idle" }, turns: [] } };
    }
    disconnect() { const active = this.connected; this.connected = false; if (active) this.emit("disconnected"); }
  }
  const fake = new FakeClient();
  const bridge = new EventBridge({ config: resolved, logger: { info() {}, warn() {}, error() {}, debug() {} }, clientFactory: () => fake });
  try {
    await bridge.start({ listen: false });
    const deadline = Date.now() + 1000;
    while (fake.resumes.length < 1 && Date.now() < deadline) await new Promise((resolve) => setTimeout(resolve, 5));
    assert.deepEqual(fake.resumes, [{ threadId: "thread-tuner", options: { developerInstructions: "Tune packaging only." } }]);
  } finally {
    await bridge.stop();
  }
});

test("W101: a Codex target identity must name an explicit role", () => {
  // The launch role is never inferred. A participant holding one role
  // today may hold two tomorrow, and that edit must not silently change
  // the persona of the session this target starts.
  const noRole = rawConfig();
  delete noRole.targets.tuner.identity.role;
  assert.throws(() => validateConfig(noRole), /identity\.role/);
  const blank = rawConfig();
  blank.targets.tuner.identity.role = "   ";
  assert.throws(() => validateConfig(blank), /identity\.role/);
});

test("W101: the instruction read refuses a launcher that lost its role", async () => {
  // Belt to the configuration's braces: readRoleInstructions is the
  // last point before a session is created or resumed, so it fails
  // closed rather than sending a role-less read.
  await assert.rejects(
    readRoleInstructions(
      { binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json" },
      { participant: "baton.tuner" },
      { execute: async () => { throw new Error("must not run"); } }),
    /needs an explicit configured role/);
});
