// codex-baton-bridge (W148, finding-v11-parallel-monitor): the
// STANDALONE v11 readiness producer — the permanent protocol-11
// adapter, launched independently beside the unchanged v10 stack
// during the certification overlap. Baton stays model-neutral and
// exposes only the participant-relative read-only wait; this external
// bridge decides how readiness schedules a Codex turn. It
// feeds the SAME local event socket and Codex target; the bridge keeps
// serializing that target's turns. One process owns v11 readiness for
// its participant; the v10 monitor keeps owning v10's.
//
// Read-only by contract: it never claims Work, answers an obligation,
// marks New, changes phase, or advances a cursor — the awakened agent
// acts through the canonical v11 CLI/JSON surface.

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { defaultEventSocketPath } from "./config.mjs";
import { sendEvent } from "./send_event.mjs";

const execFileAsync = promisify(execFile);

function usage() {
  return `usage: codex-baton-bridge --baton PATH --config PATH --participant TEAM.MEMBER --target NAME [options]

options:
  --socket PATH       event bridge Unix socket
  --wait-timeout SEC  v11 wait timeout=SECONDS (default: 60)
  --retry-ms MS       backoff after errors/unchanged sets (default: 1000)
  --once              exit after at least one event is accepted

Invokes \`BATON --config PATH --participant TEAM.MEMBER wait timeout=S\`
(protocol 11, key=value grammar) and forwards one trusted compact event
per previously unseen action key. Level-triggered: a key is suppressed
while it stays present, forgotten when it disappears, and emitted again
if it later returns. codex-baton-bridge is read-only.`;
}

function parse(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--once" || arg === "--help" || arg === "-h") {
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

function positiveInteger(value, fallback, name) {
  const selected = value === undefined ? fallback : Number(value);
  if (!Number.isSafeInteger(selected) || selected < 1) throw new Error(`${name} must be a positive integer`);
  return selected;
}

// The refuse-not-guess envelope gate (W148 R3, W207): protocol 11,
// the projection-5 contract (W179's honest breaking boundary; later
// 5.x additions welcome; 4.x, other majors, or missing refuse), the
// configured participant, a snapshot token,
// boolean timeout semantics that agree with the action set, and
// exactly the three typed action kinds — each with the locator fields
// its compact event needs and an action_key that AGREES with them.
// Anything else refuses by name; nothing is emitted for refused
// output (the v10 adapter's shape fails here by design).
export function validateEnvelope(payload, participant) {
  if (payload?.protocol_version !== 11) {
    throw new Error(`not a protocol-11 envelope (protocol_version=${payload?.protocol_version})`);
  }
  const projection = payload?.projection_version;
  const match = typeof projection === "string" && /^([0-9]+)\.([0-9]+)$/.exec(projection);
  if (!match || Number(match[1]) !== 6 || Number(match[2]) < 0) {
    throw new Error(`projection ${JSON.stringify(projection)} does not carry the projection-6 participant-action contract`);
  }
  if (payload?.participant !== participant) {
    throw new Error(`envelope participant ${JSON.stringify(payload?.participant)} is not ${participant}`);
  }
  if (typeof payload?.authority_uuid !== "string" || !payload.authority_uuid) {
    throw new Error("envelope has no authority_uuid");
  }
  if (!Number.isSafeInteger(payload?.snapshot_seq) || payload.snapshot_seq < 0) {
    throw new Error("envelope has no non-negative snapshot_seq token");
  }
  const result = payload?.result;
  if (!result || !Array.isArray(result.actionable)) {
    throw new Error("envelope has no structured result.actionable array");
  }
  if (typeof result.timed_out !== "boolean") {
    throw new Error("result.timed_out is not a boolean");
  }
  if (result.timed_out && result.actionable.length > 0) {
    throw new Error("a timed-out result carrying actions is contradictory");
  }
  const seen = new Set();
  for (const action of result.actionable) {
    if (typeof action?.action_key !== "string" || !action.action_key) {
      throw new Error("an actionable entry has no stable action_key");
    }
    if (seen.has(action.action_key)) {
      throw new Error(`duplicate action_key ${action.action_key}`);
    }
    seen.add(action.action_key);
    if (action.kind === "work") {
      if (typeof action.work !== "string" || !action.work) {
        throw new Error(`work action ${action.action_key} names no Work`);
      }
      if (action.action_key !== `work:${action.work}`) {
        throw new Error(`work action key ${action.action_key} disagrees with work ${action.work}`);
      }
      // W148 R3a: every field the TRUSTED summary consumes is typed —
      // a wrong local_id would instruct a command for the wrong Work,
      // and a string "false" claimed is truthy.
      if (action.local_id !== undefined &&
          (typeof action.local_id !== "string" || action.work !== action.local_id &&
           !action.work.endsWith(`-${action.local_id}`))) {
        throw new Error(`work action ${action.action_key} local_id ${JSON.stringify(action.local_id)} disagrees with ${action.work}`);
      }
      if (action.title !== undefined && typeof action.title !== "string") {
        throw new Error(`work action ${action.action_key} title is not a string`);
      }
      if (action.claimed !== undefined && typeof action.claimed !== "boolean") {
        throw new Error(`work action ${action.action_key} claimed is not a boolean`);
      }
    } else if (action.kind === "obligation") {
      if (!Number.isSafeInteger(action.seq) || action.seq < 1) {
        throw new Error(`obligation action ${action.action_key} has no positive seq`);
      }
      if (typeof action.work !== "string" || !action.work) {
        throw new Error(`obligation action ${action.action_key} names no Work`);
      }
      if (action.action_key !== `obligation:${action.seq}`) {
        throw new Error(`obligation action key ${action.action_key} disagrees with seq ${action.seq}`);
      }
      if (action.flavor !== undefined && typeof action.flavor !== "string") {
        throw new Error(`obligation action ${action.action_key} flavor is not a string`);
      }
    } else if (action.kind === "due_trial") {
      if (typeof action.work !== "string" || !action.work ||
          !Number.isSafeInteger(action.trial) || action.trial < 1 ||
          !Number.isSafeInteger(action.deadline_generation) || action.deadline_generation < 1) {
        throw new Error(`due_trial action ${action.action_key} lacks its positive work/trial/generation locator`);
      }
      if (action.action_key !== `trial:${action.work}:${action.trial}:${action.deadline_generation}`) {
        throw new Error(`due_trial action key ${action.action_key} disagrees with its locator`);
      }
      if (action.review_at !== undefined && typeof action.review_at !== "string") {
        throw new Error(`due_trial action ${action.action_key} review_at is not a string`);
      }
    } else {
      throw new Error(`unknown action kind ${JSON.stringify(action?.kind)} (${action.action_key})`);
    }
  }
  return payload;
}

// The compact locator: exactly what the agent needs to inspect the
// canonical v11 JSON — no discussion body, no generic instruction block.
export function actionLocator(action) {
  const locator = { kind: action.kind, action_key: action.action_key };
  if (action.work !== undefined) locator.work = action.work;
  if (action.kind === "obligation") {
    locator.obligation_seq = action.seq;
    if (action.flavor !== undefined) locator.flavor = action.flavor;
  }
  if (action.kind === "due_trial") {
    locator.trial = action.trial;
    locator.deadline_generation = action.deadline_generation;
    locator.review_at = action.review_at;
  }
  return locator;
}

function summarize(action, participant) {
  if (action.kind === "work") {
    const state = action.claimed ? "claimed by you" : "ready and unclaimed";
    const name = action.local_id ?? action.work;
    const title = action.title ? ` (${action.title})` : "";
    return `v11 Work ${name}${title} is ${state} for ${participant}. Act through the canonical v11 CLI (detail work=${name}).`;
  }
  if (action.kind === "obligation") {
    return `v11 @ obligation #${action.seq} on ${action.work} awaits ${participant}. Act through the canonical v11 CLI (obligations, respond/accept/dispose).`;
  }
  if (action.kind === "due_trial") {
    return `v11 trial ${action.trial} of ${action.work} is due (generation ${action.deadline_generation}) for ${participant}. Act through the canonical v11 CLI (detail work=${action.work}).`;
  }
  return `v11 action ${action.action_key} awaits ${participant}. Act through the canonical v11 CLI.`;
}

// One trusted compact event per action key — identity scoped by
// authority UUID, participant, and the stable action key, so the SAME
// wake never duplicates across this process's polls, while a different
// authority or participant can never collide. A RESTART deliberately
// re-emits the still-current set (rediscovery is a W148 feature); at
// most the bridge's short fingerprint window suppresses a very recent
// repeat.
export function actionEvent(envelope, action, options) {
  return {
    id: `baton-v11:${envelope.authority_uuid}:${envelope.participant}:${action.action_key}`,
    target: options.target,
    source: "baton-v11",
    type: "v11-action-ready",
    summary: summarize(action, envelope.participant),
    details: JSON.stringify(actionLocator(action), null, 2),
  };
}

function delay(ms, signal) {
  if (signal.aborted) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(done, ms);
    signal.addEventListener("abort", done, { once: true });
    function done() {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolve();
    }
  });
}

export async function codexBatonBridge(options, { signal = new AbortController().signal, runWait, execute, emitEvent = sendEvent, logger = console } = {}) {
  const waitTimeout = positiveInteger(options["wait-timeout"], 60, "--wait-timeout");
  const retryMs = positiveInteger(options["retry-ms"], 1000, "--retry-ms");
  const socket = options.socket ?? process.env.CODEX_EVENT_SOCKET ?? defaultEventSocketPath();
  // WHOLE-SET delivery memory, never one queue head: key -> delivered.
  // A key stays suppressed while present, is forgotten when the action
  // disappears, and re-emits if it later becomes actionable again. A
  // restart starts empty and rediscovers the current set. A key whose
  // forwarding failed stays undelivered and retries without loss.
  const delivered = new Map();
  while (!signal.aborted) {
    let payload;
    try {
      if (runWait) {
        payload = await runWait();
      } else {
        // W148 R4: the ONE public invocation — launcher globals, then
        // the key=value wait; the executor is injectable exactly
        // BELOW this argument construction so tests pin the argv.
        const argv = ["--config", options.config, "--participant", options.participant, "wait", `timeout=${waitTimeout}`];
        const runner = execute ?? ((file, args) => execFileAsync(file, args, { encoding: "utf8", maxBuffer: 4 * 1024 * 1024, signal }));
        const result = await runner(options.baton, argv);
        payload = JSON.parse(result.stdout);
      }
      validateEnvelope(payload, options.participant);
    } catch (error) {
      if (signal.aborted || error.name === "AbortError") break;
      logger.warn(`v11 wait failed: ${error.message}; retrying in ${retryMs}ms`);
      await delay(retryMs, signal);
      continue;
    }
    const actions = payload.result.actionable;
    // W148 R2: memory carries the SAME identity the event does —
    // authority uuid + participant + action key. An authority switch
    // therefore retires the old set atomically (its identities no
    // longer appear) and a same-named action in the new authority is
    // a genuinely new wake.
    const scope = `${payload.authority_uuid}:${payload.participant}`;
    const currentKeys = new Set(actions.map((action) => `${scope}:${action.action_key}`));
    for (const key of [...delivered.keys()]) {
      if (!currentKeys.has(key)) delivered.delete(key);
    }
    let emitted = 0;
    let failed = false;
    for (const action of actions) {
      if (delivered.get(`${scope}:${action.action_key}`)) continue;
      const event = actionEvent(payload, action, options);
      try {
        const response = await emitEvent(socket, event);
        if (!response.accepted && response.reason !== "duplicate") {
          throw new Error(`event rejected: ${JSON.stringify(response)}`);
        }
        delivered.set(`${scope}:${action.action_key}`, true);
        emitted += 1;
        logger.info(`v11 action forwarded: ${action.action_key} -> ${options.target}`);
      } catch (error) {
        failed = true;
        logger.warn(`could not forward ${action.action_key}: ${error.message}; retrying in ${retryMs}ms`);
      }
    }
    if (options.once && emitted > 0) return 0;
    if (failed) {
      await delay(retryMs, signal);
      continue;
    }
    if (!payload.result.timed_out && emitted === 0) {
      // A persistent actionable set returns immediately and unchanged:
      // back off so level-triggered suppression cannot busy-loop.
      await delay(retryMs, signal);
    }
  }
  return 0;
}

export async function runCodexBatonBridge(argv = process.argv.slice(2)) {
  const options = parse(argv);
  if (options.help || options.h) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  for (const name of ["baton", "config", "participant", "target"]) {
    if (!options[name]) throw new Error(`--${name} is required`);
  }
  const controller = new AbortController();
  process.once("SIGINT", () => controller.abort());
  process.once("SIGTERM", () => controller.abort());
  return await codexBatonBridge(options, { signal: controller.signal });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCodexBatonBridge().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`codex-baton-bridge: ${error.message}\n`);
    process.exitCode = 2;
  });
}
