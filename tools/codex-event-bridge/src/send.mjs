import { readFile } from "node:fs/promises";
import { defaultEventSocketPath } from "./config.mjs";
import { sendEvent } from "./send_event.mjs";

function usage() {
  return `usage: codex-event send --target NAME --source NAME --type NAME [options]

options:
  --socket PATH        event bridge Unix socket
  --message TEXT       event summary; stdin is used when omitted
  --details TEXT       optional details
  --details-file PATH  read optional details from a file
  --project NAME       optional project label`;
}

function parse(argv) {
  const args = argv[0] === "send" ? argv.slice(1) : [...argv];
  const values = {};
  for (let index = 0; index < args.length; index += 1) {
    const option = args[index];
    if (option === "--help" || option === "-h") return { help: true };
    if (!option.startsWith("--")) throw new Error(`unexpected argument: ${option}`);
    const value = args[++index];
    if (value === undefined) throw new Error(`${option} requires a value`);
    values[option.slice(2)] = value;
  }
  return values;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks.map((chunk) => Buffer.from(chunk))).toString("utf8").trim();
}

export async function runSend(argv = process.argv.slice(2)) {
  const options = parse(argv);
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  for (const required of ["target", "source", "type"]) {
    if (!options[required]) throw new Error(`--${required} is required`);
  }
  if (options.details && options["details-file"]) throw new Error("--details and --details-file cannot be combined");
  const summary = options.message ?? await readStdin();
  if (!summary) throw new Error("--message or non-empty stdin is required");
  const details = options["details-file"] ? await readFile(options["details-file"], "utf8") : options.details;
  const event = {
    target: options.target,
    source: options.source,
    type: options.type,
    summary,
    ...(details ? { details } : {}),
    ...(options.project ? { project: options.project } : {}),
  };
  const response = await sendEvent(options.socket ?? process.env.CODEX_EVENT_SOCKET ?? defaultEventSocketPath(), event);
  process.stdout.write(`${JSON.stringify(response)}\n`);
  return response.accepted || response.reason === "duplicate" ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSend().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`codex-event: ${error.message}\n`);
    process.exitCode = 2;
  });
}
