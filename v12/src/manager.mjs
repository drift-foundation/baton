// The trusted Worker Manager. It is the ONLY thing in this prototype
// that touches Baton, and the only thing that decides anything.
//
// The order of operations is the whole proof, so it is written out
// linearly and each step records what it just established:
//
//   observe -> offer -> read-only consent -> VALIDATE TOKEN -> canonical
//   claim -> mint assignment -> isolated writable execution -> fence ->
//   freeze -> validate -> digest -> return
//
// Nothing writable starts before the canonical claim commits, and the
// canonical claim is never attempted on an intent whose token did not
// validate. Every refusal on that path is terminal for the attempt and
// leaves the Job exactly as available as it was.

import { chmodSync, existsSync, mkdirSync, readFileSync, readdirSync,
         rmSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { join, resolve as resolvePath } from "node:path";
import { BatonClient, handlerAddress } from "./baton_cli.mjs";
import { ClaimTokenIssuer, TokenError, describeTokenMismatch } from "./claim_token.mjs";
import { ContainerAcpSession } from "./acp_session.mjs";
import { assertQuiesced, awaitQuiescence, inspect, removeAndVerify }
	from "./container.mjs";
import { diffIndex, expectedIndex } from "./fixture_check.mjs";
import { envelope, validate } from "./envelopes.mjs";
import { assertContained, manifestOf } from "./manifest.mjs";
import { copyTreeStrict, resolveInputSource } from "./input_source.mjs";
import { executionPrompt, parseFencedJson, preClaimPrompt } from "./prompts.mjs";
import { attemptPaths, assertNoBatonCapability, assertPreClaimPosture,
         disposeCredentials, executionSpec, preClaimSpec, stageCredentials }
	from "./runtime.mjs";
import { Trace } from "./trace.mjs";

class ManagerError extends Error {}

// A refusal that is a SUCCESSFUL negative outcome rather than a fault:
// the fence held. It is thrown so the happy path cannot continue, and
// caught at the top so the attempt reports `fenced` rather than `error`.
class FenceHeld extends Error {
	constructor(message, reason) { super(message); this.reason = reason; }
}

export class Manager {
	constructor(config, { now = () => Date.now(), logger = console } = {}) {
		this.config = config;
		this.now = now;
		this.logger = logger;
		this.baton = new BatonClient(config.baton);
		this.tokens = new ClaimTokenIssuer({ ttlMs: config.token.ttl_ms, now });
	}

	// Everything Baton the worker must never see. Asserted against every
	// container spec before it launches.
	// Round-4 review: this omitted `/home/sl/src/baton` and the live
	// `/home/sl/baton-v11` alias. The finding forbids runtime mounts back
	// into the Baton checkout, and the proof only caught such a mount
	// AFTER the worker had already run, by inspecting the container. A
	// safety boundary has to refuse before launch rather than depend on
	// the sample configuration being honest and notice the mistake
	// afterwards. `assertNoBatonCapability` canonicalizes both sides, so
	// naming the roots here closes direct and symlinked mounts alike.
	forbiddenPaths() {
		return [
			this.config.baton.binary,
			this.config.baton.config,
			resolvePath(this.config.baton.config, ".."),
			"/home/sl/opt/baton",
			// The live Baton source checkout this prototype must never
			// reach back into at runtime.
			"/home/sl/src/baton",
			// The production coordination home, by its versioned name and
			// by the live alias the deployment is addressed as.
			"/home/sl/baton-v11",
			"/home/sl/baton-v11.8835cd5",
			...(this.config.runtime?.forbidden_roots ?? []),
		];
	}

	async observeOnce() {
		const envelopeIn = await this.baton.wait(this.config.baton.waitTimeoutSeconds);
		const actionable = envelopeIn.result.actionable.filter(
			(action) => action.kind === "work" && !action.claimed);
		return { envelope: envelopeIn, actionable };
	}

	// One complete attempt for one actionable Job.
	async dispatch(action, { tokenFault = null, fault = null } = {}) {
		const runtimeAttempt = `${action.local_id.toLowerCase()}-${randomBytes(5).toString("hex")}`;
		const paths = attemptPaths(this.config.runtime.state_dir, runtimeAttempt);
		mkdirSync(paths.root, { recursive: true });
		const trace = new Trace(paths.trace);
		const attempt = { runtime_attempt: runtimeAttempt, runtimeAttempt, work: action.local_id,
		                  paths, trace, status: "started", tokenFault, fault,
		                  claimCommitted: false, handedOff: false };
		trace.record("attempt.start", {
			work: action.work, local_id: action.local_id,
			action_key: action.action_key, participant: this.config.baton.participant,
			token_fault: tokenFault, injected_fault: fault,
		});
		try {
			await this.attempt(action, attempt);
			// `returned-unclean` is a DISTINCT terminal state, not a
			// decoration on success. The Job did reach review and the
			// result is valid; what did not happen is cleanup, and an
			// undisposed operator credential must not be reachable only
			// by reading a trace line.
			attempt.status = attempt.status !== "started" ? attempt.status
				: (attempt.uncleanReason ? "returned-unclean" : "returned");
			// A second reap is harmless and catches anything that outlived
			// the handoff.
			await this.reap(attempt);
		} catch (error) {
			attempt.status = error instanceof FenceHeld ? "fenced" : "error";
			attempt.reason = error instanceof FenceHeld ? error.reason : "fault";
			attempt.error = error.message;
			trace.record(attempt.status === "fenced" ? "fence.held" : "attempt.error",
				{ reason: attempt.reason ?? null, message: error.message,
				  claim_committed: Boolean(attempt.claimCommitted) });
			// ORDER IS THE WHOLE POINT (review round 2). Reaping used to
			// live in a `finally` that ran AFTER compensation, so a
			// failure whose fence could not be established released the
			// Work while the previous execution container may still have
			// been running — precisely the overlap the claim boundary
			// exists to prevent. A per-attempt output mount bounds the
			// damage; it does not make two live executions of one Job
			// true or safe.
			//
			// So: reap first, and only release a Job whose old worker is
			// PROVEN gone. If that cannot be established, the canonical
			// Handler stays held and the attempt reports `stranded`.
			// Holding a claim nobody is progressing is a visible loose
			// end; advertising Work whose worker might still be alive is
			// an invisible one.
			const reaped = await this.reap(attempt);
			if (attempt.claimCommitted && !attempt.handedOff) {
				if (reaped.gone) {
					await this.compensate(attempt, error);
				} else {
					attempt.status = "stranded";
					attempt.strandedBy = reaped.reason;
					trace.record("compensation.withheld", {
						reason: reaped.reason,
						retained_credential: attempt.retainedSecret ?? null,
						note: "the execution container could not be proven gone, so "
						      + "the claim is deliberately NOT released; this Job is "
						      + "not advertised as available",
					});
				}
			}
		} finally {
			trace.record("attempt.end", { status: attempt.status });
		}
		return attempt;
	}

	// One mutation, with the ambiguity resolved rather than guessed.
	//
	// A Baton mutation carries an operation id, so an exact retry replays
	// the one committed result. That closes the ordinary lost-output
	// case. When even the retry cannot answer, the PUBLIC PROJECTION is
	// asked whether the effect is already present — `settled` decides
	// that from canonical state, not from what this process remembers
	// sending. Only if the effect is absent does the failure stand.
	async committed(attemptOnce, work, what, settled, asResult, trace,
	                observe = null) {
		try {
			return await attemptOnce();
		} catch (first) {
			trace.record(`baton.${what}.ambiguous`, { message: first.message });
			try {
				const replayed = await attemptOnce();
				trace.record(`baton.${what}.replayed`, { note: "the operation id "
					+ "replayed the committed result" });
				return replayed;
			} catch (second) {
				let state;
				try {
					state = observe ? await observe()
						: (await this.baton.detail(work)).result;
				} catch (unreadable) {
					throw new ManagerError(
						`${what} on ${work} is ambiguous (${first.message}) and the `
						+ `canonical state could not be read to settle it `
						+ `(${unreadable.message}); refusing to guess whether it committed`);
				}
				if (settled(state)) {
					trace.record(`baton.${what}.reconciled`, {
						note: "the mutation had committed; its result was lost, not its effect",
					});
					return asResult(state);
				}
				trace.record(`baton.${what}.not-committed`, {});
				throw second;
			}
		}
	}

	// Every container this attempt started, removed and PROVEN absent.
	// The pre-claim container is reaped too, but only the EXECUTION
	// container's death gates compensation: a consent turn holds no
	// claim and writes nothing, so a lingering one is untidy rather
	// than unsafe — and saying which is which is more useful than one
	// undifferentiated verdict.
	async reap(attempt) {
		const { trace, runtimeAttempt, paths } = attempt;
		const consent = await removeAndVerify(`v12poc-preclaim-${runtimeAttempt}`);
		const worker = await removeAndVerify(`v12poc-worker-${runtimeAttempt}`);
		trace.record("containers.reaped", { consent, worker });
		// The staged credential is disposed here, on EVERY path, and only
		// once BOTH containers that mount it are positively absent —
		// including the consent container, which mounts it too. An
		// undisposed secret is named in the trace rather than assumed
		// gone.
		if (consent.gone && worker.gone) {
			const disposal = disposeCredentials(paths);
			// The fact that matters is that NO credential remains, which
			// is not the same as "this call removed one": an attempt that
			// never staged one, or a second reap after a first disposed
			// it, is clean. Reading `disposed` here treated "there was
			// nothing to remove" as a failure to remove it.
			attempt.credentialsDisposed = !existsSync(paths.credentials);
			trace.record("credential.disposed", {
				...disposal, none_remains: attempt.credentialsDisposed });
		} else {
			attempt.credentialsDisposed = false;
			attempt.retainedSecret = paths.credentials;
			trace.record("credential.retained", {
				path: paths.credentials,
				reason: "a container that mounts the staged credential could not "
				        + "be proven absent, so the copy is deliberately left in "
				        + "place rather than removed from under a live process",
			});
		}
		// Round-4 review: this reported `{gone: true}` from the WORKER
		// alone, while disposal correctly required both containers. So a
		// consent container that could not be proven absent left the
		// credential on disk and still let the attempt finish as a clean
		// `returned`. Both facts now travel, and the caller decides.
		return {
			gone: worker.gone,
			clean: worker.gone && consent.gone && attempt.credentialsDisposed,
			reason: worker.gone
				? (attempt.credentialsDisposed ? null
					: `a staged credential remains at ${paths.credentials}`)
				: (worker.reason ?? "unknown"),
		};
	}

	// The bounded compensation path. It is deliberately NOT a recovery
	// subsystem: one release, compare-and-swapped against the claimant
	// the manager knows it committed, which returns the Job to exactly
	// the availability it had before the offer. If that release fails,
	// the attempt is `stranded` and says so — a stranded Job is a real
	// operational state and must not be reported as a clean end.
	async compensate(attempt, cause) {
		const { trace } = attempt;
		try {
			// Round-4 review: this was the one manager mutation still
			// making a single attempt with no identity — on the path
			// whose entire purpose is reporting whether a claim is still
			// held. A committed release whose result was lost reported
			// `stranded` while the Handler was already gone and the Job
			// was available again, which is the same ambiguity the
			// claim/pass correction removed everywhere else.
			const released = await this.committed(
				() => this.baton.release(
					attempt.work, this.config.baton.participant,
					`prototype worker manager could not complete runtime attempt `
					+ `${attempt.runtime_attempt} after claiming: ${cause.message}`,
					`v12poc-release-${attempt.runtime_attempt}`),
				attempt.work, "release",
				// Round-5 review: this asked whether NOBODY holds the Work,
				// which is transient — the next eligible member may claim
				// it between the release committing and this read, and a
				// legitimate successor Handler then made a committed
				// release look absent. The question is whether THIS
				// participant's claim is gone, and any other Handler
				// answers it.
				(state) => handlerAddress(state) !== this.config.baton.participant,
				(state) => ({ result: { released_claimant:
					this.config.baton.participant, phase: state.phase,
					successor: handlerAddress(state), reconciled: true } }),
				trace);
			attempt.status = "compensated";
			trace.record("baton.release", {
				released_claimant: released.result.released_claimant,
				reconciled: Boolean(released.result.reconciled),
				note: "post-claim failure; the Job is available again for a fresh offer",
			});
			const after = await this.baton.detail(attempt.work);
			trace.record("baton.detail.compensated", {
				phase: after.result.phase, handler: handlerAddress(after.result),
				route: after.result.route.endpoint, ready: after.result.ready,
			});
		} catch (error) {
			attempt.status = "stranded";
			attempt.strandedBy = error.message;
			trace.record("baton.release.failed", {
				message: error.message,
				retained_credential: attempt.retainedSecret ?? null,
				note: "the canonical Handler is still held; this attempt did NOT end cleanly",
			});
		}
	}

	async attempt(action, attempt) {
		const { trace, paths, runtimeAttempt } = attempt;

		// 1. Canonical state, read through the public boundary. The
		//    readiness line was a hint; this is the Job.
		const before = await this.baton.detail(action.local_id);
		trace.record("baton.detail.before", {
			phase: before.result.phase, handler: handlerAddress(before.result),
			route: before.result.route.endpoint, ready: before.result.ready,
			binding: before.result.binding?.path ?? null,
		});
		if (handlerAddress(before.result)) {
			throw new FenceHeld(
				`${action.local_id} is already handled by ${handlerAddress(before.result)}`,
				"already-claimed");
		}
		const job = await this.readJobInput(action.local_id, before, trace);

		// 2. Materialize the typed input read-only at a stable path and
		//    verify it. The digest the offer advertises is the digest of
		//    what the worker will actually see, computed here rather than
		//    copied from the Job document.
		mkdirSync(paths.input, { recursive: true });
		let copied;
		try {
			copied = copyTreeStrict(job.source, paths.input);
		} catch (error) {
			throw new FenceHeld(`the Job's typed input could not be materialized safely: `
				+ `${error.message}`, "unsafe-input");
		}
		const inputManifest = manifestOf(paths.input);
		if (job.declared_digest && job.declared_digest !== inputManifest.digest) {
			throw new FenceHeld(
				`the Job declares input digest ${job.declared_digest} but the `
				+ `materialized input is ${inputManifest.digest}`, "input-digest-mismatch");
		}
		trace.record("input.materialized", {
			path: paths.input, entries: inputManifest.entries.length,
			bytes: copied.bytes, digest: inputManifest.digest,
			followed_links: false,
		});

		// 3. Stage the per-attempt credential copy. This refuses rather
		//    than letting a worker refresh the operator's token.
		const credential = stageCredentials(paths, {
			source: this.config.runtime.credential_source,
			minRemainingMs: this.config.runtime.credential_min_remaining_ms,
			now: this.now,
		});
		trace.record("credential.staged", {
			expires_at: credential.expires_at,
			remaining_seconds: Math.round(credential.remaining_ms / 1000),
		});

		// 4. Mint the offer and its single-use token.
		// W76 review round 2: the bound finding pins "one typed
		// `directory` input and one declared `directory` result", and
		// this offered a file. Typed IN/OUT is one of the questions the
		// proof exists to settle, so the pinned contract is fulfilled
		// rather than quietly reinterpreted: the declared result is the
		// DIRECTORY, and the entries it may contain are declared with
		// it so containment still refuses anything undeclared.
		const outputPath = "/out";
		const resultEntries = ["index.json"];
		const ttl = attempt.tokenFault === "expired" ? 1 : this.config.token.ttl_ms;
		const offerBody = {
			work: action.local_id,
			participant: this.config.baton.participant,
			runtime_attempt: runtimeAttempt,
			contract_human: job.contract_human,
			inputs: [{
				name: job.input_name, type: "directory", mount: "/in",
				digest: inputManifest.digest,
				entries: inputManifest.entries.length,
				bytes: inputManifest.entries.reduce((sum, e) => sum + e.bytes, 0),
			}],
			declared_outputs: [{ name: job.result_name, type: "directory",
			                     path: outputPath, entries: resultEntries }],
			reply_format: { envelope: "claim-intent", version: "0-spike" },
			token: {},
		};
		const minted = this.tokens.mint({
			work: action.local_id, participant: this.config.baton.participant,
			runtimeAttempt, offerDigest: inputManifest.digest, ttlMs: ttl,
		});
		offerBody.token = { value: minted.token, jti: minted.payload.jti,
		                    expires_at: minted.payload.expires_at };
		// The token is now known to the trace as a secret, so any fragment
		// of it that the agent echoes back through an activity chunk is
		// scrubbed before it reaches the evidence pack.
		trace.addSecret(minted.token);
		const offer = envelope("offer", offerBody);
		mkdirSync(paths.offer, { recursive: true });
		writeFileSync(join(paths.offer, "offer.json"), `${JSON.stringify(offer, null, 2)}\n`);
		trace.record("offer.minted", {
			jti: minted.payload.jti, expires_at: minted.payload.expires_at,
			ttl_ms: ttl, declared_outputs: offer.declared_outputs,
		});
		// A genuine prior use, so the replay refusal below is the real
		// single-use rule firing rather than a simulated one.
		if (attempt.tokenFault === "replayed") {
			this.tokens.spend(minted.payload.jti);
			trace.record("token.pre-spent", { jti: minted.payload.jti,
				note: "negative case: this token has already been used once" });
		}

		// 5. The read-only pre-claim turn. No writable mount, no Baton.
		const intent = await this.preClaimTurn(offer, attempt);

		// 6. Validate. THIS is what mints authority; the agent's prose
		//    does not.
		let validated;
		try {
			validate(intent, "claim-intent");
			if (intent.decision !== "accept") {
				throw new FenceHeld(
					`the agent declined ${action.local_id}: ${intent.reason}`, "declined");
			}
			validated = this.tokens.validate(intent.token, {
				work: action.local_id,
				participant: this.config.baton.participant,
				runtime_attempt: runtimeAttempt,
			});
		} catch (error) {
			if (error instanceof FenceHeld) throw error;
			const reason = error instanceof TokenError ? error.reason : "malformed-intent";
			trace.record("token.refused", { reason, message: error.message,
				mismatch: reason === "forged"
					? describeTokenMismatch(intent.token, minted.token) : null });
			throw new FenceHeld(error.message, reason);
		}
		trace.record("token.validated", { jti: validated.jti, decision: intent.decision });

		// 7. The canonical claim. Re-read the episode first (v11's W49
		//    rule), then let the atomic claim be the arbiter.
		if (!await this.baton.episodeStillLive(action.action_key)) {
			throw new FenceHeld(
				`assignment episode ${action.action_key} is no longer live`, "episode-gone");
		}
		this.tokens.spend(validated.jti);
		// Round-3 review: `run()` makes ONE attempt and throws on a lost
		// result, so a claim that COMMITTED and whose output was lost
		// left `claimCommitted` false — the catch path then reaped the
		// worker, reconciled nothing, and reported `error` while the
		// canonical Handler was still held. This is the exact boundary
		// where a trusted manager has to know whether it owns a live
		// assignment before starting or advertising another one, so an
		// ambiguous result is resolved rather than guessed.
		const claim = await this.committed(
			() => this.baton.claim(action.local_id, `v12poc-${runtimeAttempt}`),
			action.local_id, "claim",
			(state) => handlerAddress(state) === this.config.baton.participant,
			(state) => ({ result: { claimant: handlerAddress(state),
			                        phase: state.phase, seq: state.last_change_seq,
			                        reconciled: true } }),
			trace);
		attempt.claimCommitted = true;
		trace.record("baton.claim", {
			claimant: claim.result.claimant, phase: claim.result.phase,
			seq: claim.result.seq,
		});
		// The Handler is snapshotted through a SEPARATE public read, not
		// inferred from the claim's own result: "who does Baton say is
		// executing this" is the question, and the claim result is the
		// claimant's word for it.
		const claimed = await this.baton.detail(action.local_id);
		trace.record("baton.detail.claimed", {
			phase: claimed.result.phase, handler: handlerAddress(claimed.result),
			route: claimed.result.route.endpoint, ready: claimed.result.ready,
		});

		// 8. Only now does an assignment exist.
		const assignment = envelope("assignment", {
			work: action.local_id, participant: claim.result.claimant,
			runtime_attempt: runtimeAttempt, generation: 1,
			claim_seq: claim.result.seq, claimed_at: new Date(this.now()).toISOString(),
		});
		writeFileSync(join(paths.root, "assignment.json"),
			`${JSON.stringify(assignment, null, 2)}\n`);
		trace.record("assignment.minted", { generation: assignment.generation,
			claim_seq: assignment.claim_seq });

		// 9. Isolated writable execution.
		// A deliberate fault-injection point. Proving the compensation
		// path needs a failure that happens AFTER a real canonical claim,
		// and there is no honest way to observe that without causing one.
		if (attempt.fault === "post-claim") {
			throw new ManagerError("injected post-claim fault (--fault post-claim)");
		}
		const execution = await this.executionTurn(assignment, {
			input_mount: "/in", output_path: outputPath,
			result_name: job.result_name, entries: resultEntries,
		}, attempt);

		// 10. Fence, freeze, validate, digest.
		const result = this.collect(assignment, execution, {
			inputManifest, resultEntries,
			job: { ...job, declared_outputs: offer.declared_outputs },
		}, attempt);

		// 11. CLEAN UP BEFORE HANDING OVER. Round-4 review: the handoff
		//     used to happen first and the reap afterwards, so an
		//     attempt could reach review with the operator's credential
		//     still on disk and report a clean `returned` — there is no
		//     compensation record on that path, because nothing failed.
		//     Disposal is part of the success boundary now, not tidying
		//     that happens after it.
		const cleaned = await this.reap(attempt);
		if (!cleaned.clean) {
			attempt.uncleanReason = cleaned.reason;
			trace.record("cleanup.incomplete", {
				reason: cleaned.reason,
				note: "the Job is still handed to review — the result is valid — but "
				      + "this attempt did not end clean and must not be reported as if "
				      + "it had",
			});
		}

		// 12. Return through the public boundary: recap first, then the
		//     authoritative handoff.
		await this.returnJob(action, before, result, attempt);
	}

	async readJobInput(localId, detail, trace) {
		const binding = detail.result.binding;
		if (!binding) {
			throw new FenceHeld(`${localId} has no record binding; the typed input `
				+ `has no home`, "unbound");
		}
		const resolved = await this.baton.resolve(localId);
		const recordDir = resolved.result.absolute;
		const documentPath = join(recordDir, "job.in.json");
		let document;
		try {
			document = validate(JSON.parse(readFileSync(documentPath, "utf8")), "job.in");
		} catch (error) {
			throw new FenceHeld(
				`${localId} bound record ${binding.path} has no readable job.in.json: `
				+ `${error.message}`, "unreadable-input");
		}
		const input = document.inputs[0];
		if (!input || input.type !== "directory") {
			throw new FenceHeld(`${localId} declares no directory input`, "untyped-input");
		}
		// `input.source` is an untrusted descriptor from the record, not a
		// path the manager chose. It is contained before it is used.
		let source;
		try {
			source = resolveInputSource(recordDir, input.source);
		} catch (error) {
			throw new FenceHeld(`${localId}: ${error.message}`, "unsafe-input-source");
		}
		trace.record("job.in.read", { path: documentPath, root: binding.root,
			record: binding.path, input_name: input.name, source: input.source });
		return {
			source, input_name: input.name,
			declared_digest: input.digest ?? null,
			contract_human: document.contract.human,
			result_name: document.contract.result_name,
		};
	}

	async preClaimTurn(offer, attempt) {
		const { trace, paths, runtimeAttempt } = attempt;
		const spec = assertPreClaimPosture(assertNoBatonCapability(
			preClaimSpec(this.config.runtime, paths, runtimeAttempt), this.forbiddenPaths()),
			this.config.runtime.preclaim_permission_mode);
		const chunks = [];
		const session = new ContainerAcpSession(spec, {
			permissionMode: this.config.runtime.preclaim_permission_mode,
			promptTimeoutMs: this.config.runtime.preclaim_turn_timeout_ms,
			onUpdate: (update) => {
				if (update.channel === "message") chunks.push(update.text);
				trace.record("preclaim.activity", { channel: update.channel,
					text: update.text.slice(0, 400) });
			},
		});
		let quiesced = null;
		try {
			const sessionId = await session.start();
			const state = await inspect(spec.name);
			trace.record("preclaim.container", {
				name: spec.name, id: state.id, image: state.image, user: state.user,
				network_mode: state.network_mode, session: sessionId,
				mounts: state.mounts, mode: session.modeActive,
				readonly_rootfs: state.readonly_rootfs, cap_drop: state.cap_drop,
				security_opt: state.security_opt,
			});
			const response = await session.prompt(preClaimPrompt(offer));
			trace.record("preclaim.turn", { stop_reason: response?.stopReason ?? null });
		} finally {
			await session.stop();
			quiesced = await awaitQuiescence(spec.name)
				.catch((error) => ({ error: error.message, running: null }));
			trace.record("preclaim.quiesced", quiesced);
		}
		// Outside the `finally`, so it cannot mask the turn's own failure
		// — and BEFORE the intent is even parsed, let alone claimed.
		try { assertQuiesced(quiesced, "the pre-claim container"); }
		catch (error) { throw new FenceHeld(error.message, "preclaim-not-quiescent"); }
		const text = chunks.join("");
		let intent;
		try { intent = parseFencedJson(text); }
		catch (error) {
			trace.record("preclaim.unparsable", { message: error.message,
				tail: text.slice(-400) });
			throw new FenceHeld(error.message, "unparsable-intent");
		}
		trace.record("preclaim.intent", { decision: intent.decision,
			reason: intent.reason, carried_token: typeof intent.token === "string" });
		return intent;
	}

	async executionTurn(assignment, job, attempt) {
		const { trace, paths, runtimeAttempt } = attempt;
		mkdirSync(paths.output, { recursive: true });
		const spec = assertNoBatonCapability(
			executionSpec(this.config.runtime, paths, runtimeAttempt), this.forbiddenPaths());
		const chunks = [];
		const activity = [];
		const session = new ContainerAcpSession(spec, {
			permissionMode: this.config.runtime.execution_permission_mode,
			promptTimeoutMs: this.config.runtime.execution_turn_timeout_ms,
			onUpdate: (update) => {
				if (update.channel === "message") chunks.push(update.text);
				const record = envelope("activity", {
					ts: new Date(this.now()).toISOString(),
					channel: update.channel, text: update.text.slice(0, 400),
				});
				activity.push(record);
				trace.record("worker.activity", { channel: record.channel, text: record.text });
			},
		});
		let container;
		try {
			const sessionId = await session.start();
			container = await inspect(spec.name);
			trace.record("worker.container", {
				name: spec.name, id: container.id, image: container.image,
				user: container.user, network_mode: container.network_mode,
				session: sessionId, mounts: container.mounts, mode: session.modeActive,
				readonly_rootfs: container.readonly_rootfs, cap_drop: container.cap_drop,
				security_opt: container.security_opt,
			});
			const response = await session.prompt(executionPrompt(assignment, job));
			trace.record("worker.turn", { stop_reason: response?.stopReason ?? null });
		} finally {
			// Fencing: the session is closed and the container is proven
			// stopped BEFORE anything reads the output directory.
			await session.stop();
			attempt.workerQuiescence = await awaitQuiescence(spec.name)
				.catch((error) => ({ error: error.message, running: null }));
			trace.record("worker.fenced", attempt.workerQuiescence);
		}
		// The fence is ESTABLISHED here or the attempt ends here. Reading
		// a writable output directory whose writer may still be alive is
		// exactly the boundary this is guarding.
		try { assertQuiesced(attempt.workerQuiescence, "the worker container"); }
		catch (error) { throw new FenceHeld(error.message, "worker-not-quiescent"); }
		return { text: chunks.join(""), activity, container, spec };
	}

	collect(assignment, execution, { inputManifest, resultEntries, job }, attempt) {
		const { trace, paths } = attempt;

		// The input must be exactly what it was. A worker that mutated a
		// read-only mount would invalidate everything downstream.
		const inputAfter = manifestOf(paths.input);
		if (inputAfter.digest !== inputManifest.digest) {
			throw new FenceHeld(
				`the read-only input changed during execution: ${inputManifest.digest} `
				+ `-> ${inputAfter.digest}`, "input-mutated");
		}
		trace.record("input.reverified", { digest: inputAfter.digest });

		let declared;
		try { declared = validate(parseFencedJson(execution.text), "job.out"); }
		catch (error) {
			throw new FenceHeld(`the worker declared no usable result: ${error.message}`,
				"undeclared-result");
		}
		// Shape validity is not the same as declaring THIS assignment's
		// result. Without this the manager would happily collect its own
		// hard-coded path while the worker declared a different Work and
		// no results at all — the declaration would be decoration.
		const declarationFaults = declarationProblems(declared, assignment,
			job.declared_outputs);
		trace.record("worker.declared", { summary: declared.summary,
			results: declared.results, problems: declarationFaults });
		if (declarationFaults.length) {
			throw new FenceHeld(
				`the worker's declaration does not match its assignment: `
				+ `${declarationFaults.join("; ")}`, "declaration-mismatch");
		}

		// Freeze: copy out of the writable mount, then make the copy
		// read-only. Validation runs on the frozen bytes, so nothing can
		// change between the check and the digest.
		// A previously frozen directory is read-only by construction, so
		// it has to be made removable again before it can be replaced.
		if (existsSync(paths.frozen)) {
			chmodSync(paths.frozen, 0o755);
			for (const name of readdirSync(paths.frozen)) chmodSync(join(paths.frozen, name), 0o644);
			rmSync(paths.frozen, { recursive: true, force: true });
		}
		mkdirSync(paths.frozen, { recursive: true });
		// The output directory was writable by the worker, so it is copied
		// under the same strict rules as the input: a planted symlink is
		// refused here rather than discovered downstream.
		try {
			copyTreeStrict(paths.output, paths.frozen);
		} catch (error) {
			throw new FenceHeld(`the declared result could not be frozen safely: `
				+ `${error.message}`, "unsafe-result");
		}
		for (const name of readdirSync(paths.frozen)) chmodSync(join(paths.frozen, name), 0o444);
		chmodSync(paths.frozen, 0o555);
		const outputManifest = manifestOf(paths.frozen);
		// The declared result is a directory, so containment is checked
		// over the whole tree against the entries the offer declared.
		assertContained(outputManifest, resultEntries);
		const relative = resultEntries[0];
		trace.record("result.frozen", { path: paths.frozen,
			entries: outputManifest.entries, digest: outputManifest.digest });

		// Shape, then an INDEPENDENT recomputation of the expected value.
		// The agent is never asked whether it was right.
		let parsed;
		try { parsed = JSON.parse(readFileSync(join(paths.frozen, relative), "utf8")); }
		catch (error) {
			throw new FenceHeld(`the declared result is not readable JSON: ${error.message}`,
				"unreadable-result");
		}
		const expected = expectedIndex(paths.input);
		const problems = diffIndex(parsed, expected);
		trace.record("result.checked", { independent: true, problems });
		if (problems.length) {
			throw new FenceHeld(
				`the result does not match the independently computed expectation: `
				+ problems.join("; "), "result-mismatch");
		}

		const result = envelope("result", {
			work: assignment.work, assignment,
			outputs: [{
				name: job.result_name, type: "directory", path: "/out",
				entries: resultEntries,
				digest: outputManifest.digest, manifest: outputManifest.entries,
			}],
			inputs: [{ name: job.input_name ?? "input", digest: inputManifest.digest,
			           manifest: inputManifest.entries }],
			container: {
				id: execution.container?.id ?? null,
				image: execution.container?.image ?? null,
				user: execution.container?.user ?? null,
				network_mode: execution.container?.network_mode ?? null,
				termination: attempt.workerQuiescence ?? null,
			},
			activity: execution.activity,
			status: "accepted",
		});
		writeFileSync(join(paths.root, "result.json"), `${JSON.stringify(result, null, 2)}\n`);
		attempt.result = result;
		return result;
	}

	async returnJob(action, before, result, attempt) {
		const { trace, paths } = attempt;
		const thread = before.result.threads?.[0]?.id;
		const recap = `Isolated Claude ACP worker completed ${action.local_id}. `
			+ `Result "${result.outputs[0].name}" is frozen at digest `
			+ `${result.outputs[0].digest.slice(0, 16)}… and matches the independently `
			+ `recomputed expectation. Input digest ${result.inputs[0].digest.slice(0, 16)}… `
			+ `was unchanged across execution. Runtime attempt `
			+ `${attempt.runtime_attempt}, assignment generation ${result.assignment.generation}, `
			+ `container ${(result.container.id ?? "").slice(0, 12)} terminated `
			+ `${result.container.termination?.stopped_by ?? "unknown"} with exit code `
			+ `${result.container.termination?.exit_code ?? "unknown"}. Decision now expected: `
			+ `review the frozen result and the attempt trace, then accept or reject. `
			+ `Trace: ${paths.trace}`;
		if (thread) {
			// Round-5 review: carrying an operation id made a retry
			// POSSIBLE; it did not perform one. A recap that committed and
			// lost its result threw before the pass, the outer catch
			// compensated an already-completed assignment, and the Job
			// went back on the queue to be executed a second time — with
			// a duplicate recap to follow. An identity nobody replays is
			// not effectively-once.
			//
			// It is settled from the THREAD, because that is where the
			// answer lives: either the recap is in the discussion or it is
			// not, and this manager's memory of sending it decides
			// nothing.
			const said = await this.committed(
				() => this.baton.say(thread, recap, [],
					`v12poc-recap-${attempt.runtime_attempt}`),
				action.local_id, "say",
				(messages) => messages.some((message) => message.body === recap),
				() => ({ result: { thread, reconciled: true } }),
				trace,
				async () => (await this.baton.thread(thread)).result.messages ?? []);
			trace.record("baton.say", { thread, chars: recap.length,
				reconciled: Boolean(said.result?.reconciled) });
		}
		// The mirror of the claim case, and it fails the other way: a
		// committed pass whose output was lost used to enter
		// compensation, where release refused because the Handler was
		// already gone, and the attempt reported `stranded` even though
		// the Job had reached review successfully.
		const handoff = await this.committed(
			() => this.baton.pass(action.local_id, this.config.review_endpoint,
				`isolated ACP worker returned a frozen, digest-bound result for review `
				+ `(attempt ${attempt.runtime_attempt}, output digest `
				+ `${result.outputs[0].digest.slice(0, 16)}…)`,
				`v12poc-pass-${attempt.runtime_attempt}`),
			action.local_id, "pass",
			// Same correction: an immediate claim at the DESTINATION must
			// not turn a successful handoff back into ambiguity. The
			// ruled destination route plus a Handler that is not this
			// participant proves the handoff occurred.
			(state) => state.route.endpoint === this.config.review_endpoint
				&& handlerAddress(state) !== this.config.baton.participant,
			(state) => ({ result: { to: state.route.endpoint,
			                        destination_phase: state.phase,
			                        successor: handlerAddress(state),
			                        reconciled: true } }),
			trace);
		attempt.handedOff = true;
		trace.record("baton.pass", { to: handoff.result.to,
			destination_phase: handoff.result.destination_phase });
		const after = await this.baton.detail(action.local_id);
		trace.record("baton.detail.after", {
			phase: after.result.phase, handler: handlerAddress(after.result),
			route: after.result.route.endpoint,
		});
		attempt.after = after.result;
	}
}

// Exact, positional, and closed: the declaration must name this Work and
// exactly the outputs the offer declared, in order, with no extras.
export function declarationProblems(declared, assignment, offered) {
	const problems = [];
	if (declared.work !== assignment.work) {
		problems.push(`it declares work ${JSON.stringify(declared.work)}, not `
			+ `${JSON.stringify(assignment.work)}`);
	}
	if (declared.results.length !== offered.length) {
		problems.push(`it declares ${declared.results.length} result(s), but the offer `
			+ `declared ${offered.length}`);
	}
	offered.forEach((want, index) => {
		const got = declared.results[index];
		if (!got) { problems.push(`result ${index} is missing`); return; }
		// `entries` is the manager's containment rule, not something the
		// agent restates; name/type/path are the identity it must match.
		for (const field of ["name", "type", "path"]) {
			if (got[field] !== want[field]) {
				problems.push(`result ${index} ${field} is ${JSON.stringify(got[field])}, `
					+ `not ${JSON.stringify(want[field])}`);
			}
		}
	});
	const names = declared.results.map((result) => result?.name);
	if (new Set(names).size !== names.length) {
		problems.push("it declares the same result name more than once");
	}
	return problems;
}

export { ManagerError, FenceHeld };
