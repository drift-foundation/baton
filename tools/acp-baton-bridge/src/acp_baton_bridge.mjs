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
	episodeStillLive,
	episodeVerdict,
	promptText,
	ReadinessOffers,
	validateEnvelope,
	waitOnce,
} from "./baton_readiness.mjs";
import {
	AcpAgentSession,
	DomainTeardownError,
	SessionStateError,
	TurnDeadlineError,
	preflightSessionSelection,
} from "./acp_agent_session.mjs";
import {
	launcherContract,
	readRoleInstructions,
} from "../../codex-event-bridge/src/role_instructions.mjs";
import { classifyFailure, makeRuntimePublisher }
	from "../../codex-event-bridge/src/runtime_publisher.mjs";

function usage() {
	return `usage: acp-baton-bridge --config PATH [options]

options:
  --once     exit successfully after at least one delivered wake
  --help     this text

Reads the explicit deployment configuration (agent command/args/env/
cwd, baton binary/config/participant, session policy, the exact
required permission mode, policy resources, state directory), starts
the configured ACP agent, negotiates capabilities before any session
use, and forwards one compact trusted prompt per actionable v11 key
into the configured session. Level-triggered against CANONICAL state:
an obligation, trial or poke is suppressed while present, forgotten
when it disappears, and delivered again if it returns; a ready
unclaimed Work is an OFFER that stays armed until the authority
reports the claim, is retried with bounded backoff meanwhile, and
waits while the participant's one claim slot is occupied. A returned
prompt is transport acknowledgement and never clears an offer — so
--once proves the agent path, not the claim loop. Failures (agent
exit, malformed JSON-RPC, unsupported capability, session-load
trouble) are visible and retried without discarding current
readiness.`;
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
	// W11910: the offer clock. Production reads the wall clock; a focused
	// test advances it deliberately so a retry deadline is an assertion
	// rather than a sleep.
	now = () => Date.now(),
	// W93 slice 4: the runtime lease publisher. Injectable so tests pin
	// the exact transitions and argv, and defaulted so a deployment gets
	// it without configuration.
	runtime = makeRuntimePublisher(config.baton, {
		adapter: "acp",
		provider: config.runtime?.provider,
		model: config.runtime?.model,
		actionOwner: config.runtime?.actionOwner,
		logger, signal }),
} = {}) {
	// W101: resolve the accepted role before session selection or process use.
	// Missing and ambiguous configuration is a launch refusal, never a prompt
	// an operator must remember to paste into an already-running agent.
	const role = await loadInstructions(config.baton, config.baton, { signal });
	// W14828: THE LAUNCHER CONTRACT, RENDERED ONCE FOR THE RUN, here — after
	// the configuration is accepted and before the first wait, the first
	// spawn, the first session or the first prompt.
	//
	// Once, because the alternative is rendering it per prompt from state that
	// could have moved; here, because a contract with a hole in it must refuse
	// the LAUNCH rather than produce a partial prompt some turn then acts on.
	// `launcherContract` throws on a missing or blank field and this is the
	// line that lets it: nothing downstream has to check again.
	//
	// The SHARED renderer, imported rather than re-spelled. A second textual
	// format for the same four values is how the two adapters would drift into
	// telling their contexts different things, and drift between two accounts
	// of one launcher is precisely this Work's incident.
	const launcher = launcherContract({
		binary: config.baton.binary, config: config.baton.config,
		participant: config.baton.participant, role: config.baton.role });
	// W49: the pre-turn episode revalidation is a SECOND read of the
	// same participant projection. In production that is a real
	// `timeout=0` wait against the authority. A scripted `runWait` feed
	// has no independent source to re-read — its envelope was produced
	// microseconds ago — so it revalidates against that envelope unless
	// a test injects `revalidate` to exercise the drop path deliberately.
	const stillLive = revalidate
		?? (runWait
			? async (action, envelope) => episodeVerdict(envelope, action)
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

	// W93: the lease opens BEFORE the first wait, so a runner that
	// starts and then sits idle is visibly present rather than
	// indistinguishable from one that never started. It closes in the
	// `finally` below, so an operator shutdown says goodbye instead of
	// leaving the lease to expire into `unknown`.
	await runtime.start();
	// W93 R17: publish what this bridge actually KNOWS, without
	// inference — its own process identity, the working directory the
	// deployment configured, the readiness path it polls, and the
	// session policy's root. Anything it cannot observe stays absent
	// rather than guessed, and none of it costs a provider call.
	await runtime.facts({
		service: `acp-baton-bridge pid ${process.pid}`,
		workdir: config.agent.cwd,
		readiness: config.baton.config,
	}, { source: "configured" });

	// W11910: the readiness LEVEL, cleared by the canonical claim and by
	// nothing this bridge does. A completed prompt is transport
	// acknowledgement; only `claimed:true` on a later poll answers the
	// offer. The clock is injectable so the bounded retry is pinned in
	// tests rather than slept through.
	const memory = new ReadinessOffers({ now, retryMs: config.retryMs });
	// W5: reported once per unknown kind, not once per poll — see the
	// same rule in the sibling Codex bridge.
	const reportedUnknown = new Set();
	let session = null;
	let deliveredTotal = 0;

	// R4: operator shutdown tears the child down immediately — pending
	// protocol calls reject when the subprocess dies; the loop unwinds
	// instead of waiting on an unresponsive agent.
	//
	// W28681: teardown can now REJECT, and an abort handler is not a
	// place a rejection can be handled. The failure is not lost: the
	// `finally` below tears down again on the way out and reports there.
	const onAbort = () => { session?.stop().catch(() => undefined); };
	signal.addEventListener("abort", onAbort, { once: true });

	// W28681: ONE PROCESS DOMAIN SERVES AT MOST ONE DELIVERED TURN.
	//
	// The incident: a persistent agent process accumulated tool process
	// groups across turns — four polling shells and a runaway test that
	// outlived 34-36 hours and several later turns — and nothing could
	// correlate a surviving child with the turn that made it. The bridge
	// does not launch those subprocesses and cannot enumerate them, so
	// the first boundary it can both correlate exactly and destroy
	// without PID discovery is the domain it started for this delivery.
	//
	// ACP SESSION CONTINUITY IS NOT PROCESS CONTINUITY, which is what
	// makes this legal: the run retains one session id and a replacement
	// process resumes it with `loadSession`. No rotation rule changes.
	//
	// TEARDOWN COMES BEFORE SETTLEMENT on every path — success, failure
	// and deadline alike — so `idle` is never published beside a domain
	// that is still running, and the next delivery cannot start beside
	// one either.
	const settleDomain = async (why) => {
		if (!session) return;
		const ending = session;
		session = null;
		await ending.stop();
		logger.info(`acp process domain torn down after ${why}`);
	};

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
			// An explicit transition, not a derivation: the adapter
			// OBSERVED the readiness call fail and is about to retry.
			// R8/R10: the message classifies the failure and is then
			// discarded — a readiness error can carry a URL with
			// credentials, and truncating it bounds the leak rather
			// than preventing it.
			await runtime.state("retrying", classifyFailure(error));
			await delay(config.retryMs, signal);
			continue;
		}
		// W93 R18: the level-triggered refresh signal. The adapter
		// answers it from facts it is already holding — no model turn,
		// no provider call — and the request clears when the
		// publication lands. A lost delivery simply reappears on the
		// next poll, which is what level-triggered means.
		for (const action of envelope.result.actionable) {
			if (action.kind !== "runtime_refresh") continue;
			await runtime.facts({
				service: `acp-baton-bridge pid ${process.pid}`,
				workdir: config.agent.cwd,
				readiness: config.baton.config,
			}, { source: "configured",
			     // R25: answer the exact generation asked. Two
			     // requests inside one second are two questions.
			     answers: action.generation });
		}
		for (const entry of envelope.result.ignored_actions) {
			if (reportedUnknown.has(entry.kind)) continue;
			reportedUnknown.add(entry.kind);
			logger.warn(`v11 action kind ${JSON.stringify(entry.kind)} `
				+ `is unknown to this build (first seen at `
				+ `${entry.action_key}); ignoring those entries and `
				+ `delivering the rest of the envelope`);
		}
		// A refresh is not work to forward: it never reaches the agent.
		envelope.result.actionable = envelope.result.actionable.filter(
			(action) => action.kind !== "runtime_refresh");
		const fresh = memory.sync(envelope);
		let deliveredNow = 0;
		let failed = false;
		for (const action of fresh) {
			// W28681: WHICH EPISODE THE CURRENT DOMAIN IS SERVING, reset per
			// ACTION rather than per envelope.
			//
			// Re-review [P1]: this was declared outside the loop and set only
			// after `ensureSession()` succeeded, so after one delivered action
			// a later one failing during revalidation or replacement setup
			// published the PRECEDING action's (work, episode, session).
			// Before this Work those early failures were uncorrelated; the
			// merge turned a stale local into affirmative but false operator
			// evidence, which is worse than none.
			let correlation = {};
			try {
				// W49: revalidate the exact episode IMMEDIATELY before
				// the turn. A queued prompt whose Work has since been
				// claimed, passed on or closed is STALE readiness —
				// dropped, never presented as current work. It is
				// marked delivered so this dead episode is not retried;
				// a genuinely new assignment arrives under a new key.
				const verdict = await stillLive(action, envelope);
				if (verdict === "over") {
					memory.markWithdrawn(envelope, action);
					logger.info(
						`v11 action ${action.action_key} is no longer `
						+ `actionable; dropped without invoking the agent`);
					continue;
				}
				// W11910 review [P1]: the authority says another Work
				// holds this participant's one claim. The outer snapshot
				// saw a free slot and something took it in between — an
				// interactive turn, another adapter, an operator — and
				// this read is the only place that can still know.
				//
				// NEITHER DELIVERY NOR WITHDRAWAL. The offer is still
				// good, so it is retained exactly as it is: no prompt,
				// no `markWithdrawn`, and no `markPresented`, because a
				// turn nobody spent is not an attempt. It is admitted
				// again on the next poll, and the loop's own backoff is
				// what keeps that from spinning.
				if (verdict === "deferred") {
					logger.info(
						`v11 action ${action.action_key} waits: `
						+ `${config.baton.participant} already holds a `
						+ `claim, and one participant claims one Work`);
					continue;
				}
				// W11910 re-review [P1]: the authority still names this
				// key, under a kind this build cannot act on. RETAINED
				// exactly like a deferred offer — no prompt, no
				// `markWithdrawn`, no `markPresented` — because an
				// entry this build cannot read is not an episode that
				// ended, and dropping it would clear a live level with
				// something that is not a claim.
				if (verdict === "uncertain") {
					logger.warn(
						`v11 action ${action.action_key} was answered `
						+ `under a kind this build does not know; the `
						+ `offer is retained and no turn is spent`);
					continue;
				}
				const live = await ensureSession();
				// The turn is starting, and this is the one moment the
				// bridge knows WHICH assignment episode the runner is
				// about to serve. Correlation only — the Work table
				// still decides who holds the claim.
				correlation = {
					work: action.work, episode: action.episode_seq,
					session: live.sessionId ?? undefined };
				await runtime.state("working", correlation);
				await live.promptText(promptText(envelope, action,
				                              role.instructions, launcher));
				// W28681: THE DOMAIN DIES BEFORE THE TURN IS CALLED OVER.
				// A prompt that returned says the model stopped talking;
				// it says nothing about what its tools left running.
				await settleDomain(`delivering ${action.action_key}`);
				// The turn returned. `idle` is the honest state for a
				// runner between turns; silence past the lease deadline
				// is what becomes `unknown`, and only the authority
				// derives that.
				await runtime.state("idle");
				// W11910: PRESENTED, not acknowledged. A turn that
				// returned without claiming leaves the Work ready and
				// unclaimed, and suppressing it here is exactly how
				// W6630, W6632, W6633 and W10265 sat overdue against an
				// idle runner until somebody restarted this process.
				// The offer stays armed; canonical `claimed:true` is
				// what clears it.
				memory.markPresented(envelope, action);
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
				if (error instanceof SessionStateError) {
					await runtime.state("failed", { cause: "internal",
						detail: "the configured ACP session selection "
							+ "is unusable" });
					throw error;
				}
				// W28681: an unprovable teardown is FATAL and FENCES THE
				// LANE. The readiness key is retained — no
				// `markPresented`, no `markWithdrawn` — no `idle` is
				// published, and no replacement domain is started,
				// because everything after this point would be built on
				// an assumption about a process still running.
				if (error instanceof DomainTeardownError) {
					session = null;
					await runtime.state("failed", { ...correlation,
						cause: "internal",
						detail: "could not prove the ACP agent process "
							+ "domain exited; the delivery lane is fenced" });
					throw error;
				}
				// W28681: EVERY OTHER FAILURE TEARS THE DOMAIN DOWN TOO,
				// and before it is reported. A turn that failed left
				// exactly the same descendants a turn that succeeded
				// would have, and reporting first would publish a
				// settlement beside a live domain.
				try {
					await settleDomain(`a failed ${action.action_key}`);
				} catch (teardown) {
					session = null;
					await runtime.state("failed", { ...correlation,
						cause: "internal",
						detail: "could not prove the ACP agent process "
							+ "domain exited; the delivery lane is fenced" });
					throw teardown;
				}
				// A turn that could not be delivered is a FAILED turn,
				// reported as what it is. R10: an operator cannot act on
				// "transport" when the truth is an expired credential or
				// a spent quota, so the failure is CLASSIFIED — and the
				// upstream message is read to classify and then
				// discarded, never persisted.
				//
				// W28681: a deadline keeps its `(work, episode, session)`
				// correlation, because "which assignment held the lane
				// until it timed out" is the whole operator question. It
				// is reported through the EXISTING typed
				// `failed/cause=internal`; a new runtime state to rename
				// a terminal timeout would be vocabulary rather than
				// information, and the ruling said so.
				await runtime.state("failed",
					{ ...correlation, ...classifyDelivery(error) });
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
		// W28681: the last domain goes with the bridge, and a shutdown
		// that cannot prove it is reported rather than swallowed — an
		// operator who stopped the service needs to know a domain may
		// still be running under it.
		if (session) {
			try {
				await session.stop();
			} catch (error) {
				logger.warn(`acp bridge shutdown: ${error.message}`);
				await runtime.state("failed", { cause: "internal",
					detail: "could not prove the ACP agent process domain "
						+ "exited during shutdown" });
			}
		}
		// The explicit goodbye. An operator reading Teams sees a runner
		// that exited, which is a different fact from one that stopped
		// answering — and the authority keeps those apart by provenance
		// exactly because the operator's next move differs.
		// R10: a clean exit carries NO cause — a runner that exited
		// cleanly did not fail, and `internal` is reserved for an
		// observed internal failure.
		await runtime.end({ detail: "acp bridge exited" });
	}
	return 0;
}

// The ACP permission boundary is a POLICY failure by ruling, and it is
// the one thing a bridge can observe that an operator must act on: the
// configured mode was supposed to make the request impossible. It maps
// to `approval` so an Inbox row can group it; everything else is
// classified by the shared helper, which reads the upstream message and
// then discards it.
function classifyDelivery(error) {
	// W28681: a deadline is an INTERNAL supervision decision, not a
	// transport fault and not the provider's doing. It carries this
	// adapter's own sentence so an operator reading the Inbox sees why
	// the lane was taken back rather than a generic failure.
	if (error instanceof TurnDeadlineError) {
		return { cause: "internal",
			detail: "configured ACP turn deadline exceeded; the agent "
				+ "process domain was destroyed and the delivery ended" };
	}
	if (/permission request/i.test(error?.message ?? "")) {
		return { cause: "approval",
			detail: "the agent asked for a permission the configured "
				+ "mode was supposed to make impossible" };
	}
	return classifyFailure(error);
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
