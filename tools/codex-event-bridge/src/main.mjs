import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { isAbsolute, join } from "node:path";
import { CodexClient } from "./codex_client.mjs";
import { loadConfig, validateConfig } from "./config.mjs";
import { EventBridge } from "./event_bridge.mjs";
import { formatEventMessage, normalizeEvent } from "./event_types.mjs";
import { codexDeveloperInstructions, readRoleInstructions } from "./role_instructions.mjs";
import { verifySchemaCompatibility } from "./schema_check.mjs";

const toolRoot = fileURLToPath(new URL("..", import.meta.url));

function usage() {
  return `usage: codex-event-bridge --config PATH [--debug]
       codex-event-bridge --endpoint URL --target NAME --thread ID [--debug]
       codex-event-bridge --config PATH --once [--target NAME] [--message TEXT]
       codex-event-bridge --start-thread --endpoint URL --cwd PATH --baton PATH --baton-config PATH --participant TEAM.MEMBER --role ROLE
       codex-event-bridge --endpoint URL --list-threads

options:
  --schema-dir PATH  generated schema directory
  --once             inject one test event and wait for turn/completed
  --list-threads     list recent thread IDs without resuming them
  --start-thread     create one Codex thread with accepted Baton role instructions
  --message TEXT     text for --once
  --target NAME      target selected by --once or single-target shorthand`;
}

function parse(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--debug" || arg === "--once" || arg === "--list-threads" || arg === "--start-thread" || arg === "--help" || arg === "-h") {
      options[arg.replace(/^-+/, "")] = true;
      continue;
    }
    if (!arg.startsWith("--")) throw new Error(`unexpected argument: ${arg}`);
    const value = argv[++index];
    if (value === undefined) throw new Error(`${arg} requires a value`);
    const name = arg.slice(2);
    options[name] = value;
  }
  return options;
}

function logger(debug) {
  const write = (level, message) => process.stderr.write(`${new Date().toISOString()} ${level} ${message}\n`);
  return {
    info: (message) => write("INFO", message),
    warn: (message) => write("WARN", message),
    error: (message) => write("ERROR", message),
    debug: debug ? (message) => write("DEBUG", message) : () => {},
  };
}

export async function resolveTargetInstructions(config, { read = readRoleInstructions, signal } = {}) {
  if (!config.roleInstructions) return config;
  const entries = await Promise.all(Object.entries(config.targets).map(async ([name, target]) => {
    const resolved = await read(config.roleInstructions, target.identity, { signal });
    // W12229: the accepted role prose AND this target's own launcher
    // contract. Composed HERE, from the configured source and the
    // VALIDATED identity the read just proved, so every `thread/resume`
    // reapplies it and a restart rebuilds it from current configuration
    // rather than from whatever an old thread remembers.
    //
    // `resolved.participant` and `resolved.role` rather than the
    // configured ones: `validateRoleInstructions` has already refused an
    // envelope whose participant or role disagrees, so these are the
    // values the authority itself confirmed for this target.
    const developerInstructions = codexDeveloperInstructions(
      resolved.instructions, config.roleInstructions,
      { participant: resolved.participant, role: resolved.role });
    return [name, Object.freeze({ ...target, developerInstructions, instructionRole: resolved.role, instructionGeneration: resolved.configurationGeneration })];
  }));
  return Object.freeze({ ...config, targets: Object.freeze(Object.fromEntries(entries)) });
}

async function resolveConfig(options) {
  if (options.config) return await resolveTargetInstructions(await loadConfig(options.config));
  if (options.endpoint && options.target && options.thread) {
    return validateConfig({
      servers: { local: { endpoint: options.endpoint } },
      targets: { [options.target]: { server: "local", threadId: options.thread } },
    });
  }
  throw new Error("--config is required, or provide --endpoint, --target, and --thread together");
}

function detectCodexVersion() {
  try {
    return execFileSync("codex", ["--version"], { encoding: "utf8", timeout: 5000 }).trim();
  } catch (error) {
    throw new Error(`cannot run codex --version: ${error.message}`);
  }
}

async function injectOnce(config, options, log) {
  const names = Object.keys(config.targets);
  const targetName = options.target ?? (names.length === 1 ? names[0] : null);
  if (!targetName || !config.targets[targetName]) throw new Error("--once requires --target when the config has multiple targets");
  const target = config.targets[targetName];
  const server = config.servers[target.server];
  const client = new CodexClient({ name: target.server, endpoint: server.endpoint, debug: options.debug, logger: log });
  client.on("serverRequest", (request) => log.warn(`[${targetName}] interactive request ${request.method} (${request.id}) cannot be answered by --once`));
  await client.connectAndInitialize();
  try {
    const resumed = await client.resume(target.threadId, {
      developerInstructions: target.developerInstructions,
    });
    log.info(`[${targetName}] thread resumed: ${target.threadId} (${resumed.thread.status.type})`);
    if (resumed.thread.status.type !== "idle") throw new Error(`target ${targetName} is not idle (${resumed.thread.status.type})`);
    const event = normalizeEvent({
      target: targetName,
      source: "manual-test",
      type: "external-test",
      summary: options.message ?? "External event test. Respond that you received it.",
    }, { maxDetailsBytes: config.maxDetailsBytes });
    const turn = await client.startTurn(target.threadId, formatEventMessage(event), event.id);
    log.info(`[${targetName}] turn started: ${turn.id}`);
    const completed = await client.waitForTurnCompletion(target.threadId, turn.id);
    log.info(`[${targetName}] turn completed: ${completed.id} (${completed.status})`);
    return completed.status === "completed" ? 0 : 1;
  } finally {
    client.disconnect();
  }
}

// W424 (finding-codex-bootstrap-thread-durability): the text of the
// one turn that makes a new thread durable. It is deliberately a
// no-tool instruction — the turn exists to write a rollout, not to do
// work, and a bootstrap that ran a command would be doing something
// nobody asked for in a workspace nobody has checked yet.
export const BOOTSTRAP_PROMPT =
  "Baton bootstrap. This thread was just created and needs one "
  + "recorded turn before it can be resumed. Reply with the single "
  + "word `ready` and nothing else. Do not run any command, read any "
  + "file, or use any tool.";

export async function bootstrapThread(options, log, { clientFactory, read = readRoleInstructions, out = process.stdout } = {}) {
  // W12229: `--role` joins the required operands. It was refused only
  // INDIRECTLY, by the instruction reader, so one of the four contract
  // fields failed later and in somebody else's error while the other
  // three failed here. All four are the same contract and fail in the
  // same place, before any instruction read or Codex connection.
  for (const name of ["endpoint", "cwd", "baton", "baton-config",
                      "participant", "role"]) {
    if (!options[name]) throw new Error(`--start-thread requires --${name}`);
  }
  // W12229 review [P1]: AND THE TWO PATHS ARE ABSOLUTE.
  //
  // Presence was checked and absoluteness was not, so a relative
  // `bin/baton` was accepted -- resolved by whatever launch context the
  // process happened to have -- and a relative config was read from
  // whatever working directory it happened to inherit. The block then
  // labelled those inferred locations "authoritative; do not infer",
  // which is the confirmed boundary's own rule broken by the value that
  // states it.
  //
  // THE SAME RULE THE DISPATCHER ALREADY APPLIES. `validateConfig`
  // requires both `roleInstructions` paths to be absolute; standalone
  // bootstrap never passes through that validator, so the two entry
  // points refused different shapes for the same contract. They refuse
  // the same one now, and both do it BEFORE the instruction read and
  // before any Codex connection -- a launcher operand is wrong the
  // moment it arrives, not once somebody has tried to use it.
  for (const name of ["baton", "baton-config"]) {
    if (!isAbsolute(options[name])) {
      throw new Error(`--start-thread requires --${name} to be an absolute `
        + `path; a relative one is resolved from whatever context this `
        + `process happens to have, which is the inference the launcher `
        + `contract exists to remove`);
    }
  }
  const identity = { participant: options.participant, role: options.role };
  const resolved = await read({ binary: options.baton, config: options["baton-config"] }, identity);
  const connect = clientFactory ?? ((name) => new CodexClient({ name, endpoint: options.endpoint, debug: options.debug, logger: log }));

  // W424: `thread/start` alone returns an id with no rollout behind
  // it. The bootstrap client then disconnected and the locator it had
  // just printed could not be resumed — by the dispatcher, by a
  // restarted app-server, or even by a second client one second
  // later. The command reported success for something that did not
  // exist yet.
  //
  // So the thread is MADE durable here, with one completed turn, and
  // then PROVED durable on a second connection before a single byte
  // of locator reaches stdout. Nothing about a bootstrap is urgent
  // enough to justify printing an id that might not resolve.
  const client = connect("bootstrap");
  let threadId;
  await client.connectAndInitialize();
  try {
    const started = await client.startThread({
      cwd: options.cwd,
      // W12229: the fresh context is told its four launcher values from
      // the first turn. A thread bootstrapped without them is exactly
      // the `pc.plan` context that reached W12181 repeatedly and could
      // not claim it.
      developerInstructions: codexDeveloperInstructions(
        resolved.instructions,
        { binary: options.baton, config: options["baton-config"] },
        { participant: resolved.participant, role: resolved.role }),
    });
    threadId = started.thread.id;
    log.info(`[bootstrap] thread ${threadId} created; recording its first turn`);
    const turn = await client.startTurn(threadId, BOOTSTRAP_PROMPT, randomUUID());
    const completed = await client.waitForTurnCompletion(threadId, turn.id);
    if (completed.status !== "completed") {
      throw new Error(`the bootstrap turn ended ${completed.status}; thread ${threadId} may not be resumable and is NOT reported as usable`);
    }
  } catch (error) {
    throw new Error(`could not record a first turn for ${threadId ?? "the new thread"}: ${error.message}`);
  } finally {
    client.disconnect();
  }

  // The proof is on a NEW connection, because that is exactly the
  // thing that failed: a thread readable by the client that made it
  // told the operator nothing about whether anybody else could
  // resume it.
  const verifier = connect("bootstrap-verify");
  await verifier.connectAndInitialize();
  try {
    await verifier.resume(threadId);
  } catch (error) {
    throw new Error(`thread ${threadId} was created but a second connection could not resume it: ${error.message}; not reporting an unusable locator`);
  } finally {
    verifier.disconnect();
  }
  log.info(`[bootstrap] thread ${threadId} resumed on a second connection`);
  // The one write, and it happens LAST — after the turn completed and
  // after a second connection resumed the thread. Everything before
  // this point can still refuse.
  out.write(`${JSON.stringify({ threadId, participant: resolved.participant, role: resolved.role, configurationGeneration: resolved.configurationGeneration })}\n`);
  return 0;
}

async function listThreads(endpoint, options, log) {
  if (!endpoint) throw new Error("--list-threads requires --endpoint");
  const client = new CodexClient({ name: "list", endpoint, debug: options.debug, logger: log });
  await client.connectAndInitialize();
  try {
    const result = await client.request("thread/list", { limit: 50, sortKey: "updated_at", sortDirection: "desc", archived: false });
    for (const thread of result.data) {
      const preview = thread.preview.replaceAll(/\s+/g, " ").slice(0, 80);
      process.stdout.write(`${thread.id}\t${thread.status.type}\t${thread.cwd}\t${preview}\n`);
    }
    return 0;
  } finally {
    client.disconnect();
  }
}

export async function runMain(argv = process.argv.slice(2)) {
  const options = parse(argv);
  if (options.help || options.h) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  const log = logger(options.debug);
  const schemaDir = options["schema-dir"] ?? join(toolRoot, ".codex-app-server-schema");
  await verifySchemaCompatibility(schemaDir);
  const version = detectCodexVersion();
  log.info(`detected ${version}; generated schema: ${schemaDir}`);
  if (options["start-thread"]) return await bootstrapThread(options, log);
  if (options["list-threads"]) return await listThreads(options.endpoint, options, log);
  const config = await resolveConfig(options);
  if (options.once) return await injectOnce(config, options, log);

  const bridge = new EventBridge({ config, debug: options.debug, logger: log });
  await bridge.start();
  await new Promise((resolve) => {
    let stopping = false;
    const stop = () => {
      if (stopping) return;
      stopping = true;
      resolve();
    };
    process.once("SIGINT", stop);
    process.once("SIGTERM", stop);
  });
  await bridge.stop();
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runMain().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`codex-event-bridge: ${error.message}\n`);
    process.exitCode = 2;
  });
}
