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
	episodeStillLive,
	promptText,
	validateEnvelope,
	waitOnce,
} from "./baton_readiness.mjs";
import {
	AcpAgentSession,
	SessionStateError,
	preflightSessionSelection,
} from "./acp_agent_session.mjs";
import { readRoleInstructions } from "../../codex-event-bridge/src/role_instructions.mjs";

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
	revalidate,
	loadInstructions = readRoleInstructions,
} = {}) {
	// W101: resolve the accepted role before session selection or process use.
	// Missing and ambiguous configuration is a launch refusal, never a prompt
	// an operator must remember to paste into an already-running agent.
	const role = await loadInstructions(config.baton, config.baton, { signal });
	// W49: the pre-turn episode revalidation is a SECOND read of the
	// same participant projection. In production that is a real
	// `timeout=0` wait against the authority. A scripted `runWait` feed
	// has no independent source to re-read — its envelope was produced
	// microseconds ago — so it revalidates against that envelope unless
	// a test injects `revalidate` to exercise the drop path deliberately.
	const stillLive = revalidate
		?? (runWait
			? async (action, envelope) => envelope.result.actionable.some(
				(live) => live.action_key === action.action_key)
			: (action) => episodeStillLive(config, action, { signal }));
	// One selection record for the whole run, shared by every session
	// object this bridge builds: a `load` run has it settled by the
	// preflight below, a `new` run by its first create-only publication.
	// Replacement agent processes RESUME it — see AcpAgentSession.setup.
	const runSelection = { published: false, sessionId: null };

	// W27: the session-selection preflight comes FIRST — before the
	// Baton wait and before any agent is spawned. Both a bootstrap aimed
	// at an existing selection and a load pointed at missing or unusable
	// state are launch mistakes no retry can repair, so they surface
	// immediately instead of idling as a healthy-looking loop.
	preflightSessionSelection(config, runSelection);

	const memory = new DeliveryMemory();
	// W5: reported once per unknown kind, not once per poll — see the
	// same rule in the sibling Codex bridge.
	const reportedUnknown = new Set();
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
		session = sessionFactory(config, { logger, onUpdate, runSelection });
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

	// W27 introduced a throw path OUT of this loop, so teardown can no
	// longer sit after it: an abandoned bootstrap must still kill its
	// child and drop its abort listener on the way out.
	try {
	while (!signal.aborted) {
		let envelope;
		try {
			envelope = runWait
				? await runWait()
				: await waitOnce(config, { signal });
			// The shared projection-6 gate guards EVERY path into the
			// agent — scripted test feeds included.
			validateEnvelope(envelope, config.baton.participant);
		} catch (error) {
			if (signal.aborted || error.name === "AbortError") break;
			logger.warn(`v11 wait failed: ${error.message}; retrying in `
				+ `${config.retryMs}ms`);
			await delay(config.retryMs, signal);
			continue;
		}
		for (const entry of envelope.result.ignored_actions) {
			if (reportedUnknown.has(entry.kind)) continue;
			reportedUnknown.add(entry.kind);
			logger.warn(`v11 action kind ${JSON.stringify(entry.kind)} `
				+ `is unknown to this build (first seen at `
				+ `${entry.action_key}); ignoring those entries and `
				+ `delivering the rest of the envelope`);
		}
		const fresh = memory.sync(envelope);
		let deliveredNow = 0;
		let failed = false;
		for (const action of fresh) {
			try {
				// W49: revalidate the exact episode IMMEDIATELY before
				// the turn. A queued prompt whose Work has since been
				// claimed, passed on or closed is STALE readiness —
				// dropped, never presented as current work. It is
				// marked delivered so this dead episode is not retried;
				// a genuinely new assignment arrives under a new key.
				if (!await stillLive(action, envelope)) {
					memory.markDelivered(envelope, action);
					logger.info(
						`v11 action ${action.action_key} is no longer `
						+ `actionable; dropped without invoking the agent`);
					continue;
				}
				const live = await ensureSession();
				await live.promptText(promptText(envelope, action,
				                              role.instructions));
				memory.markDelivered(envelope, action);
				deliveredNow += 1;
				deliveredTotal += 1;
				logger.info(
					`v11 action delivered: ${action.action_key} -> `
					+ `${config.baton.participant}'s configured session`);
			} catch (error) {
				// W27: a session-selection fault is FATAL, never
				// retried. Losing the create-only race means this
				// bootstrap's session is already abandoned; looping
				// would spawn agent after agent against a selection
				// that belongs to the winner.
				if (error instanceof SessionStateError) throw error;
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
	} finally {
		signal.removeEventListener("abort", onAbort);
		if (session) await session.stop();
	}
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
