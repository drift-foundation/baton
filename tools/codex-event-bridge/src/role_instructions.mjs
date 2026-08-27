// W101: the one launcher-facing role-instruction projection. Both Codex and
// ACP adapters invoke the same accepted Baton configuration through its public
// CLI; neither reads baton.json or the authority store directly.

import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export function validateRoleInstructions(payload, identity) {
  if (payload?.protocol_version !== 11) throw new Error(`not a protocol-11 instruction envelope (protocol_version=${payload?.protocol_version})`);
  const projection = payload?.projection_version;
  const match = typeof projection === "string" && /^([0-9]+)\.([0-9]+)$/.exec(projection);
  const major = match ? Number(match[1]) : null;
  // W5: projection 12 moved the major for the `poke` action kind; the
  // role-instruction result itself did not change, so this consumer
  // widens in the same candidate rather than refusing a shape it can
  // still read.
  if (!match || ![9, 10, 11, 12].includes(major)) {
    throw new Error(`projection ${JSON.stringify(payload?.projection_version)} does not carry the v11 role-instruction contract`);
  }
  if (payload?.participant !== identity.participant) {
    throw new Error(`instruction envelope participant ${JSON.stringify(payload?.participant)} is not ${identity.participant}`);
  }
  if (typeof payload?.authority_uuid !== "string" || !payload.authority_uuid) throw new Error("instruction envelope has no authority_uuid");
  const result = payload?.result;
  if (!result || result.participant !== identity.participant) throw new Error("instruction result does not name the configured participant");
  if (typeof result.role !== "string" || !result.role) throw new Error("instruction result has no selected role");
  if (identity.role !== undefined && result.role !== identity.role) {
    throw new Error(`instruction result selected role ${result.role}, not configured role ${identity.role}`);
  }
  if (typeof result.instructions !== "string" || !result.instructions.trim()) throw new Error("instruction result has no non-empty instructions");
  if (!Number.isSafeInteger(result.configuration_generation) || result.configuration_generation < 1) {
    throw new Error("instruction result has no positive configuration_generation");
  }
  return Object.freeze({
    authorityUuid: payload.authority_uuid,
    participant: result.participant,
    role: result.role,
    instructions: result.instructions,
    configurationGeneration: result.configuration_generation,
  });
}

export async function readRoleInstructions(source, identity, { execute, signal } = {}) {
  // W101: role= is always sent. The reader refuses without it, so a
  // launcher that lost its configured role fails closed here rather
  // than starting a session with an unintended persona.
  if (typeof identity.role !== "string" || !identity.role.trim()) {
    throw new Error(`launching ${identity.participant} needs an explicit configured role`);
  }
  const argv = ["--config", source.config, "--participant", identity.participant,
                "instructions", `role=${identity.role}`];
  const runner = execute ?? ((file, args) => execFileAsync(file, args, { encoding: "utf8", maxBuffer: 4 * 1024 * 1024, signal }));
  const completed = await runner(source.binary, argv);
  let payload;
  try {
    payload = JSON.parse(completed.stdout);
  } catch (error) {
    throw new Error(`Baton instructions returned invalid JSON: ${error.message}`);
  }
  return validateRoleInstructions(payload, identity);
}


// W12229: THE BATON LAUNCHER CONTRACT, rendered for a CODEX context.
//
// `work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/
//  finding-pc-central-runner-stack/findings/finding-codex-launcher-contract/`
//
// W12181 reached a fresh `pc.plan` Codex context again and again and could
// not be claimed, because that context had been told WHAT to do and never
// told WHICH executable, config, participant and role to do it with. The
// launcher held all four and passed only the accepted role prose to
// `thread/start`.
//
// The values were not missing from the deployment; they were dropped at the
// carrier. `baton.codex` happened to work because a role author had copied a
// deployment sentence into durable persona prose, which is configuration
// content and not an adapter guarantee — and W12181 is the counterexample.
//
// WHY DEVELOPER INSTRUCTIONS ARE THE CARRIER. The generated app-server
// contract exposes `developerInstructions` on `thread/start` and every
// `thread/resume` and exposes NO per-thread environment map; the generic
// per-thread `config` override is the one W415 ruled out. One app-server
// process hosts every Baton and Pushcoin target, so process environment
// would cross participant boundaries even if a launcher could set it after
// start. Developer instructions are the participant-specific carrier that
// already exists and is already reapplied on every resume.
//
// SHARED BY BOTH ADAPTER FAMILIES, and that is why this is a separate
// function rather than a change to `readRoleInstructions`. The reader above
// returns accepted role prose ALONE; each family composes this block beside
// it, in the carrier its own transport actually has:
//
//   Codex   into `developerInstructions`, for the reasons just above — one
//           app-server process hosts every target and there is no per-thread
//           environment map;
//   ACP     into every readiness prompt, and the same four values derived
//           into the spawned child's environment. See
//           `acp-baton-bridge/src/acp_baton_bridge.mjs`, which imports this
//           function and renders it once per run.
//
// W12229 RULED ACP'S CARRIER TO BE FOUR EXPLICIT `agent.env` VALUES, and this
// paragraph said so — correctly, then. W14828 superseded that on carrier
// SUFFICIENCY after a live incident: a healthy restart rendered the correct
// four values into the runtime context, the prompt named none of them, the
// operator template spelled none of them, and the fresh model went looking —
// found a persistent participant file still pinned to a retired deployment,
// and made its first `claim` through an executable that refused the live
// authority. Environment delivery remains useful and must agree; it is no
// longer the model's only locator.
//
// The earlier ruling is kept here rather than erased because it is how the
// next reader knows why the current rule is not the obvious one: this block
// is composed into ACP prompts DELIBERATELY, and removing that composition
// would restore the incident.
//
// EXACTLY THE RULED FOUR. Not `identity.actionOwner`, not the exec-policy
// path, not configuration contents, not credentials, not any ambient
// environment: this function reads nothing, searches nothing, and defaults
// nothing.
export function launcherContract({ binary, config, participant, role }) {
  for (const [name, value] of [["binary", binary], ["config", config],
                               ["participant", participant], ["role", role]]) {
    // FAIL CLOSED rather than render a block with a hole in it. A context
    // told three of the four values would infer the fourth, and inferring is
    // the exact thing the confirmed boundary forbids.
    if (typeof value !== "string" || !value.trim()) {
      throw new Error(`the Baton launcher contract needs an explicit ${name}`);
    }
  }
  // JSON-QUOTED, so a space, a quote or a control character in a path is
  // DATA rather than instruction syntax a model has to guess the end of.
  return [
    "Baton launcher contract (authoritative; do not infer):",
    `BATON_BIN=${JSON.stringify(binary)}`,
    `BATON_CONFIG=${JSON.stringify(config)}`,
    `BATON_PARTICIPANT=${JSON.stringify(participant)}`,
    `BATON_ROLE=${JSON.stringify(role)}`,
    "Invoke BATON_BIN with --config BATON_CONFIG and --participant "
    + "BATON_PARTICIPANT for every Baton operation.",
  ].join("\n");
}

/** The developer instructions one Codex context receives: its accepted role
 *  prose, and beneath it the four launcher values that prose may not assume.
 *
 *  The block goes LAST on purpose. Role prose is a persona and can be long;
 *  the contract is short, exact, and the thing a context needs to find. */
export function codexDeveloperInstructions(instructions, source, identity) {
  return `${instructions}\n\n${launcherContract({
    binary: source.binary, config: source.config,
    participant: identity.participant, role: identity.role })}`;
}
