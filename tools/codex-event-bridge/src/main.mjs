import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { CodexClient } from "./codex_client.mjs";
import { loadConfig, validateConfig } from "./config.mjs";
import { EventBridge } from "./event_bridge.mjs";
import { formatEventMessage, normalizeEvent } from "./event_types.mjs";
import { verifySchemaCompatibility } from "./schema_check.mjs";

const toolRoot = fileURLToPath(new URL("..", import.meta.url));

function usage() {
  return `usage: codex-event-bridge --config PATH [--debug]
       codex-event-bridge --endpoint URL --target NAME --thread ID [--debug]
       codex-event-bridge --config PATH --once [--target NAME] [--message TEXT]
       codex-event-bridge --endpoint URL --list-threads

options:
  --schema-dir PATH  generated schema directory
  --once             inject one test event and wait for turn/completed
  --list-threads     list recent thread IDs without resuming them
  --message TEXT     text for --once
  --target NAME      target selected by --once or single-target shorthand`;
}

function parse(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--debug" || arg === "--once" || arg === "--list-threads" || arg === "--help" || arg === "-h") {
      options[arg.replace(/^-+/, "")] = true;
      continue;
    }
    if (!arg.startsWith("--")) throw new Error(`unexpected argument: ${arg}`);
    const value = argv[++index];
    if (value === undefined) throw new Error(`${arg} requires a value`);
    options[arg.slice(2)] = value;
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

async function resolveConfig(options) {
  if (options.config) return await loadConfig(options.config);
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
    const resumed = await client.resume(target.threadId);
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
