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
