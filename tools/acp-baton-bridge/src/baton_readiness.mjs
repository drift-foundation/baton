// Baton readiness, isolated from ACP process/session handling (the
// pinned slice-A boundary). The canonical projection-6 envelope
// contract is SHARED with the sibling Codex bridge — one validator,
// imported, never re-typed here — so both external products refuse the
// same malformed output by the same names.

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import {
	actionLocator,
	MAX_OFFER_RETRY_MS,
	ReadinessOffers,
	validateEnvelope,
} from "../../codex-event-bridge/src/codex_baton_bridge.mjs";

// W11910: the claim-aware readiness level is ONE rule for both adapter
// families, so it is imported from the same module the envelope
// validator comes from rather than re-typed here. The defect it
// corrects was identical on both sides, and a second copy is how the
// two would drift back apart.
export { actionLocator, MAX_OFFER_RETRY_MS, ReadinessOffers, validateEnvelope };

const execFileAsync = promisify(execFile);

// One compact trusted line per action — the SAME turn-input shape the
// Codex path renders, agent-generic: locator plus the standing-policy
// cue plus accepted role instructions, no discussion bodies or event-supplied
// instruction block.
export function promptText(envelope, action, roleInstructions = null,
                           launcher = null) {
	const participant = envelope.participant;
	let summary;
	if (action.kind === "work") {
		const state = action.claimed ? "claimed by you" : "ready and unclaimed";
		const name = action.local_id ?? action.work;
		const title = action.title ? ` (${action.title})` : "";
		summary = `v11 Work ${name}${title} is ${state} for ${participant}. Act through the canonical v11 CLI (detail work=${name}).`;
	} else if (action.kind === "obligation") {
		summary = `v11 @ obligation #${action.seq} on ${action.work} awaits ${participant}. Act through the canonical v11 CLI (obligations, respond/accept/dispose).`;
	} else if (action.kind === "poke") {
		// W5 slice B. Deliberately ordinary wording, matching the Codex
		// path word for word: the approved contract calls a poke a
		// lightweight request for status between collaborators, and
		// says it must not read as an alarm, an escalation, or an
		// automated health verdict. So it names who asked, repeats
		// their actual question, and points at the one verb that
		// answers it.
		summary = `${action.asker} asks ${participant}: ${action.request} Answer through the canonical v11 CLI (poke-answer poke=${action.poke} state=idle|working|waiting|needs-help explanation=…), reading your canonical Baton state first.`;
	} else {
		summary = `v11 trial ${action.trial} of ${action.work} is due (generation ${action.deadline_generation}) for ${participant}. Act through the canonical v11 CLI (detail work=${action.work}).`;
	}
	const operating = roleInstructions
		? ` Configured role instructions: ${roleInstructions}` : "";
	const line = `[BATON READY] ${summary}${operating} Apply standing v11 Baton policy.`;
	// W14828: THE LAUNCHER CONTRACT RIDES EVERY PROMPT, and it goes LAST for
	// the reason the Codex path already gives — role prose is a persona and
	// can be long, while the contract is short, exact, and the thing a context
	// needs to find.
	//
	// It is here because the role prose above says a deployment "supplies the
	// exact Baton binary and explicit config" and then names neither. A fresh
	// model told that much and no more does the reasonable thing: it goes
	// looking, and what it finds is a persistent participant file whose
	// deployment pin outlived the deployment. That is the incident, and no
	// amount of prose fixes it — the values have to BE here.
	//
	// Rendered by the caller from the accepted configuration and passed in, so
	// this stays the pure text function it was. A caller with no block renders
	// none rather than half of one; startup is where an incomplete contract is
	// refused, and by the time a prompt is built the block already exists.
	return launcher ? `${line}\n\n${launcher}` : line;
}

// The ONE public Baton invocation — launcher globals then the key=value
// wait; the executor is injectable so tests pin the exact argv.
export async function waitOnce(config, { execute, signal, timeout } = {}) {
	const seconds = timeout ?? config.baton.waitTimeoutSeconds;
	const argv = ["--config", config.baton.config,
	              "--participant", config.baton.participant,
	              "wait", `timeout=${seconds}`];
	const runner = execute ?? ((file, args) => execFileAsync(
		file, args,
		{ encoding: "utf8", maxBuffer: 4 * 1024 * 1024, signal }));
	const result = await runner(config.baton.binary, argv);
	const payload = JSON.parse(result.stdout);
	return validateEnvelope(payload, config.baton.participant);
}

// W49: readiness is an EDGE TO RE-EVALUATE, never authority to act
// from an old envelope. A prompt can sit queued behind a long turn —
// observed live at ~12 minutes — by which time the Work may have been
// claimed, passed on, closed or superseded. Immediately before the
// agent turn starts, re-read the participant projection with
// `timeout=0` and require this EXACT episode key to still be present.
// A missing key means the episode is over: drop it and continue,
// mutating no Work. This narrows but cannot close the window — a
// mutation can still win between this read and the agent's claim — so
// the agent's mandatory atomic claim remains the final authority and
// fails closed. That is why this is a cheap read, not a lock.
export async function episodeStillLive(config, action, options = {}) {
	const envelope = await waitOnce(config, { ...options, timeout: 0 });
	return episodeVerdict(envelope, action);
}

/** W11910 review [P1]: `over`, `deferred` or `live`, from one canonical read.
 *
 *  A BOOLEAN COULD NOT SAY THIS. `false` meant the episode was over and
 *  withdrew the offer permanently; `true` started the turn. An offer that is
 *  still perfectly good but waiting on somebody else's claim is neither, and
 *  answering `true` spent a model turn against a slot the authority had
 *  already given away — a claim taken by another adapter, an interactive
 *  turn, or an operator between the outer poll and this read.
 *
 *  THE CURRENT MATCHING ENTRY DECIDES, with its kind and its current claimed
 *  state, rather than anything the caller remembered:
 *
 *    absent            the episode is over — unless the key is present
 *                      under a kind this build does not know, which is
 *                      unreadable rather than withdrawn (`uncertain`)
 *    not a Work        live; the one-claim Work slot does not govern
 *                      obligations, trials, pokes or refreshes
 *    a claimed Work    live; it is the participant's own assignment being
 *                      recovered, and it can never wait behind itself
 *    an unclaimed Work deferred while any Work claim occupies the slot,
 *                      and live otherwise
 */
export function episodeVerdict(envelope, action) {
	const live = envelope.result.actionable;
	const matched = live.find(
		(entry) => entry.action_key === action.action_key);
	if (!matched) {
		// ABSENT FROM WHAT WAS KEPT IS NOT THE SAME AS WITHDRAWN.
		//
		// W11910 re-review [P1], ruled for the Codex dispatcher and true of
		// this read for the same reason. The envelope contract is
		// deliberately liberal about kinds this build does not know: it drops
		// them from the actionable set and records them under
		// `ignored_actions` so a newer authority can add a primitive without
		// breaking an older bridge. That tolerance is about DELIVERY — this
		// build cannot act on a kind it has never heard of — and it says
		// nothing about whether the episode is over. An entry carrying the
		// exact key is the authority still naming it, so reading its removal
		// as withdrawal would clear a live level with something that is not a
		// claim, which is the whole defect this Work exists to correct.
		if (envelope.result.ignored_actions?.some(
				(entry) => entry.action_key === action.action_key)) {
			return "uncertain";
		}
		return "over";
	}
	if (matched.kind !== "work" || matched.claimed === true) return "live";
	// `matched` is a current unclaimed Work, so any claimed Work here is
	// necessarily another one and the slot is spoken for.
	return live.some((entry) => entry.kind === "work"
	                 && entry.claimed === true) ? "deferred" : "live";
}
