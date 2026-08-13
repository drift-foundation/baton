import { spawn } from "node:child_process";
import { defaultEventSocketPath } from "./config.mjs";
import { sendEvent } from "./send_event.mjs";

function parse(argv) {
  const options = { source: "build", maxOutputBytes: 32 * 1024, notifySuccess: false };
  let index = 0;
  for (; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--") {
      index += 1;
      break;
    }
    if (!arg.startsWith("--")) break;
    if (arg === "--notify-success") {
      options.notifySuccess = true;
      continue;
    }
    const value = argv[++index];
    if (value === undefined) throw new Error(`${arg} requires a value`);
    if (arg === "--target") options.target = value;
    else if (arg === "--source") options.source = value;
    else if (arg === "--socket") options.socket = value;
    else if (arg === "--project") options.project = value;
    else if (arg === "--max-output-bytes") options.maxOutputBytes = Number(value);
    else throw new Error(`unknown option: ${arg}`);
  }
  options.command = argv.slice(index);
  if (!options.target) throw new Error("--target is required");
  if (options.command.length === 0) throw new Error("a command is required");
  if (!Number.isSafeInteger(options.maxOutputBytes) || options.maxOutputBytes < 1024) throw new Error("--max-output-bytes must be an integer of at least 1024");
  return options;
}

function appendTail(current, chunk, limit) {
  const combined = Buffer.concat([current, Buffer.from(chunk)]);
  return combined.length <= limit ? combined : combined.subarray(combined.length - limit);
}

function displayCommand(command) {
  return command.map((part) => JSON.stringify(part)).join(" ");
}

export async function runAndNotify(argv = process.argv.slice(2)) {
  const options = parse(argv);
  const [program, ...args] = options.command;
  let output = Buffer.alloc(0);
  let spawnError = null;
  const child = spawn(program, args, { stdio: ["inherit", "pipe", "pipe"] });
  child.stdout.on("data", (chunk) => {
    process.stdout.write(chunk);
    output = appendTail(output, chunk, options.maxOutputBytes);
  });
  child.stderr.on("data", (chunk) => {
    process.stderr.write(chunk);
    output = appendTail(output, chunk, options.maxOutputBytes);
  });
  child.once("error", (error) => { spawnError = error; });
  const result = await new Promise((resolve) => child.once("close", (code, signal) => resolve({ code, signal })));
  const succeeded = !spawnError && result.code === 0;
  if (!succeeded || options.notifySuccess) {
    const status = spawnError ? `could not start: ${spawnError.message}` : result.signal ? `terminated by ${result.signal}` : `exited with status ${result.code}`;
    const event = {
      target: options.target,
      source: options.source,
      type: succeeded ? "build-succeeded" : "build-failed",
      summary: `${displayCommand(options.command)} ${status}`,
      details: `Command: ${displayCommand(options.command)}\nResult: ${status}\n\nLast output:\n${output.toString("utf8")}`,
      ...(options.project ? { project: options.project } : {}),
    };
    try {
      const response = await sendEvent(options.socket ?? process.env.CODEX_EVENT_SOCKET ?? defaultEventSocketPath(), event);
      if (!response.accepted && response.reason !== "duplicate") process.stderr.write(`run-and-notify: event rejected: ${JSON.stringify(response)}\n`);
    } catch (error) {
      process.stderr.write(`run-and-notify: notification failed: ${error.message}\n`);
    }
  }
  if (spawnError) return 127;
  if (result.signal) return 128;
  return result.code ?? 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runAndNotify().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`run-and-notify: ${error.message}\n`);
    process.exitCode = 2;
  });
}
