// acp-baton-bridge (W163, finding-v11-acp-agent-bridge): the external
// ACP readiness client. Canonical v11 participant-relative `wait` on
// one side; ONE configured ACP agent session over JSON-RPC/stdio on
// the other:
//
//     baton wait JSON -> acp-baton-bridge -> ACP agent over stdio
//
// Baton stays model-neutral; this program owns ACP initialization,
// session selection, prompt submission, streamed updates, the ruled
// permission boundary, and process supervision. It is read-only with
// respect to readiness: it never claims Work, answers obligations,
// advances cursors, or closes anything for the agent. Agent-generic by
// contract — Claude, Gemini, or any conforming agent differ only in
// deployment configuration.

import { loadConfig } from "./config.mjs";
import {
	DeliveryMemory,
	promptText,
	validateEnvelope,
	waitOnce,
} from "./baton_readiness.mjs";
import { AcpAgentSession } from "./acp_agent_session.mjs";

function usage() {
	return `usage: acp-baton-bridge --config PATH [options]

options:
  --once     exit successfully after at least one delivered wake
  --help     this text

Reads the explicit deployment configuration (agent command/args/env/
cwd, baton binary/config/participant, session policy, the exact
required permission mode, policy resources, state directory), starts
the configured ACP agent, negotiates capabilities before any session
use, and forwards one compact trusted prompt per previously unseen
v11 action key into the configured session. Level-triggered: a key is
suppressed while present, forgotten when it disappears, and delivered
again if it returns. Failures (agent exit, malformed JSON-RPC,
unsupported capability, session-load trouble) are visible and retried
without discarding current readiness.`;
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

export async function runBridge(config, {
	signal = new AbortController().signal,
	runWait,
	sessionFactory = (cfg, hooks) => new AcpAgentSession(cfg, hooks),
	logger = console,
	once = false,
	onUpdate,
} = {}) {
	const memory = new DeliveryMemory();
	let session = null;
	let deliveredTotal = 0;

	// R4: operator shutdown tears the child down immediately — pending
	// protocol calls reject when the subprocess dies; the loop unwinds
	// instead of waiting on an unresponsive agent.
	const onAbort = () => { session?.stop(); };
	signal.addEventListener("abort", onAbort, { once: true });

	const ensureSession = async () => {
		// R2: reuse ONLY a fully published session — one whose
		// initialize, session new/load, and exact mode enforcement all
		// succeeded and whose subprocess is still alive.
		if (session && session.alive()) return session;
		if (session) await session.stop();
		session = sessionFactory(config, { logger, onUpdate });
		try {
			const sessionId = await session.start();
			logger.info(`acp session ready: ${sessionId} `
				+ `(mode ${config.permissionMode})`);
			return session;
		} catch (error) {
			// A failed setup is never retained for reuse.
			await session.stop();
			session = null;
			throw error;
		}
	};

	while (!signal.aborted) {
		let envelope;
		try {
			envelope = runWait
				? await runWait()
				: await waitOnce(config, { signal });
			// The shared projection-5 gate guards EVERY path into the
			// agent — scripted test feeds included.
			validateEnvelope(envelope, config.baton.participant);
		} catch (error) {
			if (signal.aborted || error.name === "AbortError") break;
			logger.warn(`v11 wait failed: ${error.message}; retrying in `
				+ `${config.retryMs}ms`);
			await delay(config.retryMs, signal);
			continue;
		}
		const fresh = memory.sync(envelope);
		let deliveredNow = 0;
		let failed = false;
		for (const action of fresh) {
			try {
				const live = await ensureSession();
				await live.promptText(promptText(envelope, action));
				memory.markDelivered(envelope, action);
				deliveredNow += 1;
				deliveredTotal += 1;
				logger.info(
					`v11 action delivered: ${action.action_key} -> `
					+ `${config.baton.participant}'s configured session`);
			} catch (error) {
				// The key stays undelivered; readiness is never
				// discarded by a failed turn, exit, or policy failure.
				failed = true;
				logger.warn(`could not deliver ${action.action_key}: `
					+ `${error.message}; retrying in ${config.retryMs}ms`);
			}
		}
		if (once && deliveredTotal > 0) break;
		if (failed) {
			await delay(config.retryMs, signal);
			continue;
		}
		if (!envelope.result.timed_out && deliveredNow === 0) {
			// A persistent unchanged actionable set returns
			// immediately: back off so suppression cannot busy-loop.
			await delay(config.retryMs, signal);
		}
	}
	signal.removeEventListener("abort", onAbort);
	if (session) await session.stop();
	return 0;
}

export async function runAcpBatonBridge(argv = process.argv.slice(2)) {
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
	if (options.help || options.h) {
		process.stdout.write(`${usage()}\n`);
		return 0;
	}
	if (!options.config) throw new Error("--config is required");
	const config = loadConfig(options.config);
	const controller = new AbortController();
	process.once("SIGINT", () => controller.abort());
	process.once("SIGTERM", () => controller.abort());
	return await runBridge(config, {
		signal: controller.signal,
		once: Boolean(options.once),
	});
}

if (import.meta.url === `file://${process.argv[1]}`) {
	runAcpBatonBridge().then((code) => { process.exitCode = code; },
		(error) => {
			process.stderr.write(`acp-baton-bridge: ${error.message}\n`);
			process.exitCode = 2;
		});
}
