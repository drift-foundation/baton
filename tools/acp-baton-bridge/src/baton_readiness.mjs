// Baton readiness, isolated from ACP process/session handling (the
// pinned slice-A boundary). The canonical projection-6 envelope
// contract is SHARED with the sibling Codex bridge — one validator,
// imported, never re-typed here — so both external products refuse the
// same malformed output by the same names.

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import {
	actionLocator,
	validateEnvelope,
} from "../../codex-event-bridge/src/codex_baton_bridge.mjs";

export { actionLocator, validateEnvelope };

const execFileAsync = promisify(execFile);

// One compact trusted line per action — the SAME turn-input shape the
// Codex path renders, agent-generic: locator plus the standing-policy
// cue, no bodies, no generic instruction block.
export function promptText(envelope, action) {
	const participant = envelope.participant;
	let summary;
	if (action.kind === "work") {
		const state = action.claimed ? "claimed by you" : "ready and unclaimed";
		const name = action.local_id ?? action.work;
		const title = action.title ? ` (${action.title})` : "";
		summary = `v11 Work ${name}${title} is ${state} for ${participant}. Act through the canonical v11 CLI (detail work=${name}).`;
	} else if (action.kind === "obligation") {
		summary = `v11 @ obligation #${action.seq} on ${action.work} awaits ${participant}. Act through the canonical v11 CLI (obligations, respond/accept/dispose).`;
	} else {
		summary = `v11 trial ${action.trial} of ${action.work} is due (generation ${action.deadline_generation}) for ${participant}. Act through the canonical v11 CLI (detail work=${action.work}).`;
	}
	return `[BATON READY] ${summary} Apply standing v11 Baton policy.`;
}

// WHOLE-SET level-triggered delivery memory, identity-scoped exactly
// like the Codex bridge (W148 R2): authority uuid + participant +
// action key. Suppressed while present, forgotten when gone, re-emitted
// on return; a failed delivery keeps its key undelivered.
export class DeliveryMemory {
	constructor() {
		this.delivered = new Map();
	}

	sync(envelope) {
		const scope = `${envelope.authority_uuid}:${envelope.participant}`;
		const current = new Set(envelope.result.actionable.map(
			(action) => `${scope}:${action.action_key}`));
		for (const key of [...this.delivered.keys()]) {
			if (!current.has(key)) this.delivered.delete(key);
		}
		return envelope.result.actionable.filter((action) =>
			!this.delivered.get(`${scope}:${action.action_key}`));
	}

	markDelivered(envelope, action) {
		const scope = `${envelope.authority_uuid}:${envelope.participant}`;
		this.delivered.set(`${scope}:${action.action_key}`, true);
	}
}

// The ONE public Baton invocation — launcher globals then the key=value
// wait; the executor is injectable so tests pin the exact argv.
export async function waitOnce(config, { execute, signal } = {}) {
	const argv = ["--config", config.baton.config,
	              "--participant", config.baton.participant,
	              "wait", `timeout=${config.baton.waitTimeoutSeconds}`];
	const runner = execute ?? ((file, args) => execFileAsync(
		file, args,
		{ encoding: "utf8", maxBuffer: 4 * 1024 * 1024, signal }));
	const result = await runner(config.baton.binary, argv);
	const payload = JSON.parse(result.stdout);
	return validateEnvelope(payload, config.baton.participant);
}
