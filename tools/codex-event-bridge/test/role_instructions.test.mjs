import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { resolveTargetInstructions } from "../src/main.mjs";
import { launcherContract, readRoleInstructions, validateRoleInstructions } from "../src/role_instructions.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";

// W415: the dispatcher refuses to start unless the deployment-owned
// execpolicy file authorizes each managed participant's canonical Baton
// operations. These fixtures therefore need a real one.
import { mkdtempSync as _mkdtemp, writeFileSync as _write } from "node:fs";
import { join as _join } from "node:path";
import { inspectionRules as _inspectionRules,
         rulesFor as _rulesFor } from "../src/exec_policy.mjs";
const _policyDir = _mkdtemp("/tmp/w415-fixture-policy-");
export const FIXTURE_POLICY = _join(_policyDir, "baton.rules");
// W2845: and the deployment-wide read-only Docker inspection profile,
// which `start()` preflights on the same nominated file.
_write(FIXTURE_POLICY, ["/srv/baton/baton.json", "/home/op/baton.json"]
	.flatMap((config) => ["baton.tuner", "baton.codex", "a.b"]
		.flatMap((participant) => _rulesFor({
			binary: "/opt/baton/bin/baton", config, participant })))
	.concat(_inspectionRules())
	.join("\n") + "\n");


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
    roleInstructions: { binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json",
			execPolicyFile: FIXTURE_POLICY },
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      tuner: { server: "local", threadId: "thread-tuner", identity: { participant: "baton.tuner", role: "tuner", actionOwner: "ops.slaw" } },
    },
    eventSocket: "/tmp/codex-role-instructions-test.sock",
    quarantineDir: freshQuarantineDir(),
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
    identity: { participant: "baton.tuner", role: "review", actionOwner: "ops.slaw" },
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
    // W415: no per-thread config overrides — the capability comes from a
    // deployment-owned execpolicy file, so resume sends instructions only.
    //
    // W12229 replaced the value, and the old one is the defect: resume
    // reapplied the role prose and NOTHING else, so a restarted context
    // was told what to be and never which executable, config,
    // participant or role to act with. It is composed now, and rebuilt
    // from the current configured source and the accepted read rather
    // than from anything the thread remembers.
    assert.deepEqual(fake.resumes, [{ threadId: "thread-tuner",
      options: { developerInstructions: "Tune packaging only.\n\n"
        + launcherContract({ binary: "/opt/baton/bin/baton",
          config: "/srv/baton/baton.json", participant: "baton.tuner",
          role: "tuner" }) } }]);
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


// -- W12229: the launcher contract, per target and never crossing -------------

test("two Codex targets receive their OWN participant and role, never each "
  + "other's", async () => {
  // The confirmed boundary's second acceptance: each context receives
  // only its own identity. Both targets share one binary and one config,
  // which is the case where crossing would be invisible.
  const raw = rawConfig();
  raw.targets.planner = { server: "local", threadId: "thread-planner",
    identity: { participant: "pc.plan", role: "rview", actionOwner: "ops.slaw" } };
  const resolved = await resolveTargetInstructions(validateConfig(raw), {
    read: async (_source, identity) => ({ ...identity,
      instructions: `prose for ${identity.participant}`,
      configurationGeneration: 3 }),
  });
  const tuner = resolved.targets.tuner.developerInstructions;
  const planner = resolved.targets.planner.developerInstructions;
  assert.match(tuner, /BATON_PARTICIPANT="baton.tuner"/);
  assert.match(tuner, /BATON_ROLE="tuner"/);
  assert.equal(tuner.includes("pc.plan"), false,
    "the tuner context was told another participant's identity");
  assert.match(planner, /BATON_PARTICIPANT="pc.plan"/);
  assert.match(planner, /BATON_ROLE="rview"/);
  assert.equal(planner.includes("baton.tuner"), false,
    "the planner context was told another participant's identity");
});

test("the block is rebuilt from the CURRENT configured source, not remembered",
  async () => {
  // A restart or a configuration refresh re-resolves; nothing about an
  // earlier target object or an old thread's text is authoritative.
  const first = await resolveTargetInstructions(validateConfig(rawConfig()), {
    read: async (_source, identity) => ({ ...identity,
      instructions: "prose", configurationGeneration: 3 }),
  });
  const raw = rawConfig();
  raw.roleInstructions.binary = "/opt/baton/v11/next/bin/baton";
  const second = await resolveTargetInstructions(validateConfig(raw), {
    read: async (_source, identity) => ({ ...identity,
      instructions: "prose", configurationGeneration: 4 }),
  });
  assert.match(first.targets.tuner.developerInstructions,
    /BATON_BIN="\/opt\/baton\/bin\/baton"/);
  assert.match(second.targets.tuner.developerInstructions,
    /BATON_BIN="\/opt\/baton\/v11\/next\/bin\/baton"/);
});

test("the contract carries the ACCEPTED participant and role, which the read "
  + "already proved", async () => {
  // `validateRoleInstructions` refuses an envelope whose participant or
  // role disagrees with the configured identity, so by here the two are
  // one fact. This asserts the composition uses the proved value rather
  // than re-deriving it, and that the refusal above it is untouched.
  await assert.rejects(resolveTargetInstructions(validateConfig(rawConfig()), {
    read: async () => { throw new Error("instruction envelope participant "
      + '"somebody.else" is not baton.tuner'); },
  }), /is not baton\.tuner/);
});

test("a target whose deployment supplies no role source keeps its old shape",
  async () => {
  // No `roleInstructions` means no accepted role read and no contract to
  // compose from: the config is returned untouched rather than gaining a
  // block invented from nothing.
  const raw = rawConfig();
  delete raw.roleInstructions;
  delete raw.targets.tuner.identity;
  const config = validateConfig(raw);
  assert.equal(await resolveTargetInstructions(config), config);
});

test("the ACP adapter's shared read still returns accepted prose alone",
  async () => {
  // THE ASSERTION IS UNCHANGED AND THE EXPLANATION IS NOT. The launcher block
  // is composed BESIDE this read by each adapter, never inside it -- which is
  // exactly the property that lets ONE rendering serve both families rather
  // than two drifting apart.
  //
  // What this comment used to say was that the block was Codex-only and that
  // an ACP prompt carrying one would be a leak across a boundary. W12229 made
  // that true; W14828 superseded its carrier sufficiency after the live drift
  // incident, and ACP composes the same block into every readiness prompt on
  // purpose. The assertion below was right either way -- the read returns role
  // prose ALONE -- so only the reasoning around it needed correcting.
  const resolved = await readRoleInstructions(
    { binary: "/opt/baton/bin/baton", config: "/srv/baton/baton.json" },
    { participant: "baton.tuner", role: "tuner" },
    { execute: async () => ({ stdout: JSON.stringify(envelope()) }) });
  assert.equal(resolved.instructions.includes("BATON_BIN"), false,
    "the shared instruction read grew a launcher block of its own; each "
    + "adapter composes one beside this prose, and folding it in here would "
    + "give the two families one carrier they cannot vary");
});


test("every surface that documents the launcher names both ACP carriers",
async () => {
	// THE GENERALISATION TWO ROUNDS OF THIS POINT AT.
	//
	// Round one corrected the source paragraph and gated it. Round two found
	// the same superseded claim in this bridge's README, which that gate did
	// not look at, and gated that. There is a third surface -- the ACP
	// bridge's own README -- and nothing compares it to anything either.
	//
	// The rule is one rule, so this checks it in one place across every file
	// that publishes it: each must name BOTH ACP carriers, and none may
	// declare the block Codex-only or the environment sufficient. A fourth
	// document tomorrow is the only way this goes stale again.
	const { readFileSync } = await import("node:fs");
	const { fileURLToPath } = await import("node:url");
	const { dirname, join } = await import("node:path");
	const here = dirname(fileURLToPath(import.meta.url));
	const surfaces = {
		"codex README": join(here, "..", "README.md"),
		"acp README": join(here, "..", "..", "acp-baton-bridge", "README.md"),
		"the shared renderer": join(here, "..", "src",
		                            "role_instructions.mjs"),
	};
	for (const [name, path] of Object.entries(surfaces)) {
		const text = readFileSync(path, "utf8");
		assert.match(text, /prompt/i, `${name} does not mention the prompt`);
		assert.doesNotMatch(text, /Codex-only/i,
			`${name} still declares the launcher block Codex-only`);
		assert.doesNotMatch(text, /would be one\s+family's mechanism leaking/,
			`${name} still calls the ACP prompt carrier a leak`);
	}
});

test("every launcher documentation surface names the ACP prompt and environment",
async () => {
  // The adjacent all-surfaces case originally checked only `prompt` despite
  // claiming both carriers. Pin the other half independently: deleting the
  // derived child environment from any published contract must be visible.
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const here = dirname(fileURLToPath(import.meta.url));
  const surfaces = {
    "codex README": join(here, "..", "README.md"),
    "acp README": join(here, "..", "..", "acp-baton-bridge", "README.md"),
    "the shared renderer": join(here, "..", "src",
                                "role_instructions.mjs"),
  };
  for (const [name, path] of Object.entries(surfaces)) {
    const published = readFileSync(path, "utf8");
    assert.match(published, /readiness prompt/i,
      `${name} lost the authoritative ACP prompt carrier`);
    assert.match(published, /environment/i,
      `${name} lost the derived ACP environment carrier`);
  }
});

test("the shared renderer's stated consumers are its actual consumers",
async () => {
	// W14828 review [P2]. The paragraph beside `launcherContract` said the
	// renderer was CODEX-ONLY and warned that composing it into ACP prompts
	// would be wrong -- while the ACP bridge imported it and composed it into
	// every prompt. Source-level contract documentation that contradicts the
	// code tells the next maintainer to remove the composition that fixes a
	// live incident.
	//
	// It drifted because nothing compared it to anything. This is that
	// comparison: BOTH families import this function, so the comment cannot
	// go back to naming one of them without a case going red.
	const { readFileSync } = await import("node:fs");
	const { fileURLToPath } = await import("node:url");
	const { dirname, join } = await import("node:path");
	const here = dirname(fileURLToPath(import.meta.url));
	const renderer = readFileSync(
		join(here, "..", "src", "role_instructions.mjs"), "utf8");
	const codex = readFileSync(
		join(here, "..", "src", "codex_baton_bridge.mjs"), "utf8");
	const acp = readFileSync(
		join(here, "..", "..", "acp-baton-bridge", "src",
		     "acp_baton_bridge.mjs"), "utf8");

	// The ACP adapter really does import and render it.
	assert.match(acp, /launcherContract/,
		"the ACP bridge no longer consumes the shared renderer");
	assert.match(acp, /role_instructions\.mjs/);
	// And the Codex side still composes it into developer instructions.
	assert.match(renderer, /codexDeveloperInstructions/);
	assert.ok(codex.length > 0);

	// The stale claim, in the exact forms it took.
	const paragraph = renderer.slice(0, renderer.indexOf("export function launcherContract"));
	assert.doesNotMatch(paragraph, /CODEX-ONLY/,
		"the shared renderer declares itself Codex-only again");
	assert.doesNotMatch(paragraph, /only the Codex paths compose this/,
		"the shared renderer claims one consumer again");
	// And the reader it sits beside still returns role prose ALONE, which is
	// the property that lets one renderer serve two carriers.
	assert.match(paragraph, /accepted role prose ALONE/i);
});

test("the user-facing launcher docs name both ACP carriers", async () => {
	// W14828 independent re-review: fixing only the source comment leaves the
	// published bridge contract telling operators the opposite rule. The ACP
	// adapter now carries the shared block in every readiness prompt AND derives
	// the same values into the child environment; neither carrier is sufficient
	// alone.
	const { readFileSync } = await import("node:fs");
	const { fileURLToPath } = await import("node:url");
	const { dirname, join } = await import("node:path");
	const here = dirname(fileURLToPath(import.meta.url));
	const readme = readFileSync(join(here, "..", "README.md"), "utf8");
	assert.match(readme, /ACP[\s\S]{0,300}environment variables/,
		"the shared README lost the derived ACP environment carrier");
	assert.match(readme, /ACP[\s\S]{0,800}readiness prompt/,
		"the shared README lost the authoritative ACP prompt carrier");
	assert.doesNotMatch(readme, /It is Codex-only/,
		"the shared README still declares the launcher block Codex-only");
	assert.doesNotMatch(readme,
		/ACP's ruled contract is its four `agent\.env` values/,
		"the shared README still publishes the superseded environment-only rule");
});
