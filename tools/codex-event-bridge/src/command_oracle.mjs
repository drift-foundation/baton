// W2845: what a policy matrix case is allowed to conclude from one turn.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/
// finding-managed-docker-inspection-policy/`
//
// THE ORACLE DEFECT THIS EXISTS TO CLOSE. The matrix used to observe only
// the METHODS of server requests arriving during a turn: a ruled inspection
// passed when that list was empty and an unruled command passed when it was
// not. An empty list proves that no approval RPC reached the client. It does
// not distinguish a policy-declined command from a model that never attempted
// one — and the operator run produced an empty list for all eight cases,
// which is exactly the ambiguity.
//
// The same hole is on the positive side and is easier to miss: "no approval
// arrived" is not "the inspection ran". A matrix that cannot tell an allowed
// command from an unattempted one is not measuring the boundary at all.
//
// WHAT REPLACES IT. The installed app-server returns each turn's items from
// `thread/read` with `includeTurns: true`. A `commandExecution` item carries
// the exact `command`, its `source`, a terminal `status` of `completed`,
// `failed` or `declined`, and an `exitCode`. An approval request carries
// `threadId`, `turnId` and `itemId`, so a denial can be CORRELATED to the
// exact item rather than counted as an unrelated request.
//
// So every verdict below is about one identified command item, and the
// approval evidence is joined to it by identity.
//
// PURE ON PURPOSE. Nothing here connects to anything: it takes a turn, a
// requested command and the approvals observed, and returns a verdict. That
// is what lets the six item shapes and the two approval shapes be driven
// deterministically instead of hoped for during a live run.

export const AGENT_SOURCE = "agent";
const TERMINAL = new Set(["completed", "failed", "declined"]);

/** The ONE server request that is command-execpolicy evidence.
 *
 *  Re-review [P1]: correlation by `threadId`/`turnId`/`itemId` alone is
 *  necessary and NOT sufficient. The installed schema gives
 *  `item/fileChange/requestApproval` and `item/permissions/requestApproval`
 *  the same three identity fields, so a request about a completely different
 *  boundary was being read as proof that command policy refused — which can
 *  accept an unruled case whose command merely FAILED, the exact state this
 *  oracle otherwise refuses.
 *
 *  Spelled exactly as the schema spells it. The synthetic fixtures used
 *  `commandExecution/requestApproval`, and method-blind correlation hid that:
 *  a name nothing compares cannot be wrong. */
export const COMMAND_APPROVAL_METHOD =
	"item/commandExecution/requestApproval";

/** Every agent-sourced command item in one turn.
 *
 *  A MISSING `source` IS `agent`, and that is read off the installed
 *  schema rather than assumed: `CommandExecutionThreadItem` lists `source`
 *  with `"default": "agent"` and does NOT require it, while `command`,
 *  `id`, `status` and `type` are required. An item that omits it is the
 *  ordinary agent case — and dropping it here would report a ruled
 *  inspection that ran perfectly as "the model never attempted the
 *  command", which is the exact ambiguity this oracle exists to remove. */
export function commandItems(turn) {
	return (turn?.items ?? []).filter(
		(item) => item?.type === "commandExecution"
		          && (item.source ?? AGENT_SOURCE) === AGENT_SOURCE);
}

/** The ONE item a case is about, or why there is not one.
 *
 *  Zero items means the model never proved an attempt, which is the
 *  operator run's ambiguity and is a FAILURE rather than a pass on either
 *  side. More than one matching item, or any item running something else,
 *  means the case's instruction — run exactly this and nothing else — was
 *  not followed, and a verdict drawn from it would be about a different
 *  command. */
export function requestedItem(turn, command) {
	const items = commandItems(turn);
	if (items.length === 0) {
		return { item: null, fault: "no agent command item: the model never "
		                            + "proved it attempted the command" };
	}
	const matching = items.filter((item) => item.command === command);
	const other = items.filter((item) => item.command !== command);
	if (matching.length === 0) {
		return { item: null,
		         fault: `the turn ran ${JSON.stringify(other.map((i) => i.command))} `
		                + `and never ${JSON.stringify(command)}` };
	}
	if (matching.length > 1) {
		return { item: null,
		         fault: `the turn ran ${JSON.stringify(command)} `
		                + `${matching.length} times; one case is one command` };
	}
	if (other.length > 0) {
		return { item: null,
		         fault: `the turn also ran ${JSON.stringify(other.map((i) => i.command))}, `
		                + `so this verdict would not be about one command` };
	}
	return { item: matching[0], fault: null };
}

/** The COMMAND approvals that belong to this exact item.
 *
 *  Correlation by identity AND by method, not by count. An approval request
 *  raised by something else in the same run says nothing about this command
 *  — counting it was the first half of the defect, and matching only its
 *  identity was the second, because two other approval kinds carry the same
 *  three fields. */
export function approvalsFor(approvals, { threadId, turnId, item }) {
	return (approvals ?? []).filter((approval) => {
		if (approval?.method !== COMMAND_APPROVAL_METHOD) return false;
		const params = approval?.params ?? {};
		if (params.itemId === undefined || item?.id === undefined) return false;
		return params.threadId === threadId
		       && params.turnId === turnId
		       && params.itemId === item.id;
	});
}

/** Whether the client actually SENT the denial for one of these requests.
 *
 *  Re-review [P1]: `respondError` returns false when it cannot send — a
 *  closed socket, a missing id — and the matrix ignored it. An observed
 *  request the client never answered is not a denial, and describing it as
 *  one turns an unanswered prompt into proof that policy refused. */
export function deniedApprovals(correlated) {
	return correlated.filter((approval) => approval?.denied === true);
}

/** A ruled inspection: it RAN, it succeeded, and nothing asked permission. */
export function ruledInspectionOutcome({ turn, command, approvals,
                                         threadId, turnId }) {
	const { item, fault } = requestedItem(turn, command);
	if (fault) return { ok: false, why: fault };
	const correlated = approvalsFor(approvals, { threadId, turnId, item });
	if (correlated.length > 0) {
		return { ok: false,
		         why: `the ruled inspection asked for approval `
		              + `(${correlated.map((a) => a.method).join(", ")})` };
	}
	if (item.status !== "completed") {
		return { ok: false,
		         why: `the ruled inspection is ${item.status}, not completed` };
	}
	if (item.exitCode !== 0) {
		return { ok: false,
		         why: `the ruled inspection exited ${item.exitCode}` };
	}
	return { ok: true, why: `completed exit 0, no approval (item ${item.id})` };
}

/** An unruled command: the boundary refused it, and it is visible WHICH way.
 *
 *  Two shapes are acceptable and they are different events. The sandbox may
 *  decline the command outright, or it may raise an approval request that
 *  the client denies — the dispatcher denies them, so the matrix does too —
 *  after which the item must reach a terminal state that is not `completed`.
 *
 *  A BARE `failed` IS NOT REFUSAL and is the trap this rule exists for: an
 *  attempted Docker command can fail on its own merits, and reading that as
 *  a policy boundary would make the matrix pass on a broken daemon. */
export function unruledRefusalOutcome({ turn, command, approvals,
                                        threadId, turnId }) {
	const { item, fault } = requestedItem(turn, command);
	if (fault) return { ok: false, why: fault };
	const correlated = approvalsFor(approvals, { threadId, turnId, item });
	if (item.status === "completed") {
		return { ok: false,
		         why: `the unruled command COMPLETED (exit ${item.exitCode}); `
		              + `the boundary let it through` };
	}
	if (correlated.length > 0) {
		const denied = deniedApprovals(correlated);
		if (denied.length === 0) {
			return { ok: false,
			         why: `a command approval was observed but the denial was `
			              + `never sent; an unanswered prompt is not a refusal` };
		}
		if (!TERMINAL.has(item.status)) {
			return { ok: false,
			         why: `the denied approval left the item ${item.status}, `
			              + `which is not terminal` };
		}
		return { ok: true,
		         why: `command approval requested and denied, item `
		              + `${item.status} (item ${item.id})` };
	}
	if (item.status === "declined") {
		return { ok: true, why: `declined without an approval request `
		                        + `(item ${item.id})` };
	}
	return { ok: false,
	         why: `the item is ${item.status} with no correlated approval; `
	              + `a command can fail on its own, so this does not prove `
	              + `the boundary refused it` };
}

/** W7830: the READINESS SHAPE — a read, then the mandatory claim, as two
 *  separate execution requests.
 *
 *  `work/records/2026/08/finding-managed-turn-single-authority-call/`.
 *
 *  A managed turn batched `detail` and `claim` into one `exec_command`. The
 *  read ran, the mutation stayed inside the ordinary workspace sandbox and
 *  failed with a read-only database, and the Work stayed unclaimed. The
 *  deployment authorizes an EXACT canonical invocation, so a batch containing
 *  one is a different command — which is why the fix is a rule about command
 *  SHAPE and the proof has to be about shape too.
 *
 *  WHAT AN OUTCOME ALONE CANNOT SAY. "The Work is claimed" is compatible with
 *  one batched command that happened to work, with a claim issued before the
 *  read, and with three attempts of which one landed. None of those is the
 *  boundary. So this verdict is about the ORDERED LIST of agent command
 *  items: exactly two, the second exactly the canonical claim, both terminal
 *  and completed, and no command approval correlated to either.
 *
 *  Deliberately separate from `requestedItem`, which requires exactly ONE
 *  item and would refuse this shape as "the turn also ran something else".
 *  One command per turn was right for the policy matrix; this Work is about
 *  the turn that legitimately runs two. */
export function readinessClaimOutcome({ turn, readCommand, claimCommand,
                                        approvals, threadId, turnId }) {
	const items = commandItems(turn);
	if (items.length !== 2) {
		return { ok: false,
		         why: `the turn ran ${items.length} agent command items `
		              + `${JSON.stringify(items.map((i) => i.command))}; the `
		              + `readiness shape is exactly two, a read then the claim` };
	}
	const [read, claim] = items;
	// ORDER IS THE WHOLE POINT. A claim issued first is not the batch defect,
	// but it is not this shape either, and a proof that accepted it would
	// stop being about "one operation per request, in the order the turn
	// needs them".
	if (read.command !== readCommand) {
		return { ok: false,
		         why: `the first command was ${JSON.stringify(read.command)}, `
		              + `not the canonical read` };
	}
	if (claim.command !== claimCommand) {
		return { ok: false,
		         why: `the second command was ${JSON.stringify(claim.command)}, `
		              + `not the canonical claim` };
	}
	for (const [what, item] of [["read", read], ["claim", claim]]) {
		if (!TERMINAL.has(item.status)) {
			return { ok: false,
			         why: `the ${what} item is ${item.status}, which is not `
			              + `terminal` };
		}
		if (item.status !== "completed") {
			return { ok: false,
			         why: `the ${what} item ${item.status} (exit `
			              + `${item.exitCode}); the standalone operation was `
			              + `supposed to succeed on its own` };
		}
		// AND ITS EXIT CODE. Review [P1]: `completed` says the command RAN to
		// termination, not that it worked — so a `detail` exiting 7 beside a
		// claim exiting 0 was reported as the readiness shape. The Handler
		// assertion afterwards can catch a claim that did not commit; nothing
		// could catch a failed read, which is the half this Work is about,
		// because the batched invocation failed on its MUTATION and the read
		// is what succeeded.
		if (item.exitCode !== 0) {
			return { ok: false,
			         why: `the ${what} item completed with exit `
			              + `${item.exitCode}; completed is that it ran, not `
			              + `that it worked` };
		}
	}
	for (const [what, item] of [["read", read], ["claim", claim]]) {
		const correlated = approvalsFor(approvals, { threadId, turnId, item });
		if (correlated.length > 0) {
			return { ok: false,
			         why: `the ${what} asked for approval (item ${item.id}); a `
			              + `standalone canonical operation needs none` };
		}
	}
	return { ok: true,
	         why: `two standalone agent commands, read then claim, both `
	              + `completed with no approval (items ${read.id}, ${claim.id})` };
}

/** A BOUNDED account of what a turn actually did, for a verdict that failed.
 *
 *  W2845 review 2026-08-23 item 3. The operator run recorded eight cases with
 *  no exact command item and retained no transcript, so the reason was not
 *  recoverable afterwards — which is how a fail-closed rejection becomes
 *  un-diagnosable rather than merely negative.
 *
 *  BOUNDED IN EVERY DIMENSION. Review [P2]: the first version capped each
 *  agent message and nothing else — every item type, every message and every
 *  full command string were emitted, so a turn with a thousand commands
 *  produced a one-megabyte summary. A cap on the parts is not a bound on the
 *  whole, and the moment it mattered would be the moment a model went
 *  off-script, which is exactly when an operator log must stay readable.
 *
 *  So the caps are HARD and PRIVATE. A caller-supplied `limit` may only make
 *  the per-item cap SMALLER; it cannot raise it, because an exported helper
 *  that can be made unbounded by its caller is unbounded.
 *
 *  TRUE TOTALS ARE ALWAYS REPORTED, even when the lists are cut. A diagnostic
 *  that silently drops 990 commands is worse than one that says it dropped
 *  them: the count is often the finding.
 *
 *  The exclusions are the design: `reasoning` items contribute their TYPE and
 *  nothing else, only `agentMessage` text is quoted, and only THIS turn is
 *  read. It says what happened and decides nothing — no verdict reads it, and
 *  adding one would make prose evidence again. */
const MAX_ITEM_TYPES = 40;
const MAX_AGENT_MESSAGES = 5;
const MAX_COMMANDS = 10;
const MAX_MESSAGE_CHARS = 400;
const MAX_COMMAND_CHARS = 200;
// EVERY OTHER STRING THAT CROSSES IN. Review [P2] round 2: the counts were
// capped and the item-type strings were not, so ONE item with a
// million-character `type` produced a million-character summary. Protocol
// values are small, and a hard property that depends on the protocol being
// obeyed is a property of the protocol, not of this helper.
const MAX_LABEL_CHARS = 60;
// The backstop. MEASURED AS INERT TODAY, and kept anyway: with every field
// capped above, the summary can no longer reach it, so a mutation removing it
// changes nothing and it is not counted as a guard. It is here for the next
// field somebody adds without a cap — the failure this round corrected twice
// was exactly a new string arriving uncapped beside capped ones.
const MAX_SUMMARY_CHARS = 4000;

function clip(text, cap) {
	const value = String(text ?? "");
	return value.length > cap
		? `${value.slice(0, cap)}… (${value.length} chars)` : value;
}

/** A caller may only TIGHTEN, and only with a real number.
 *
 *  Review [P2] round 2: `Math.min(NaN, hardMaximum)` is NaN, and
 *  `value.length > NaN` is false — so `limit: NaN` disabled the cap entirely
 *  and returned whole million-character strings. A clamp that a non-number
 *  walks through is not a clamp, and the failure direction was OFF, which is
 *  the one that never announces itself. */
function tighten(limit, hardMaximum) {
	if (typeof limit !== "number" || !Number.isFinite(limit)) {
		return hardMaximum;
	}
	const floored = Math.floor(limit);
	return floored < 1 ? hardMaximum : Math.min(floored, hardMaximum);
}

function take(values, cap) {
	return values.length > cap
		? [...values.slice(0, cap), `… (${values.length - cap} more of `
		                            + `${values.length})`]
		: values;
}

export function missingAttemptDiagnostic({ turn, turnId, limit = null }) {
	const messageCap = tighten(limit, MAX_MESSAGE_CHARS);
	const commandCap = tighten(limit, MAX_COMMAND_CHARS);
	const label = (value) => clip(value, MAX_LABEL_CHARS);
	if (!turn) {
		return { turnId: turnId === undefined || turnId === null
		                 ? null : label(turnId),
		         status: null, itemTypes: [], agentMessages: [], commands: [],
		         totals: { items: 0, agentMessages: 0, commands: 0 },
		         summary: clip(`no recorded turn `
		                       + `${turnId === undefined || turnId === null
		                          ? "(unknown)" : label(turnId)}`,
		                       MAX_SUMMARY_CHARS) };
	}
	const items = turn.items ?? [];
	const allTypes = items.map((item) => label(item?.type ?? "unknown"));
	const allMessages = items
		.filter((item) => item?.type === "agentMessage")
		.map((item) => clip(item.text, messageCap));
	const allCommands = commandItems(turn)
		.map((item) => `${label(item.status)} `
		               + `${JSON.stringify(clip(item.command, commandCap))}`);
	const totals = { items: allTypes.length,
	                 agentMessages: allMessages.length,
	                 commands: allCommands.length };
	const itemTypes = take(allTypes, MAX_ITEM_TYPES);
	const agentMessages = take(allMessages, MAX_AGENT_MESSAGES);
	const commands = take(allCommands, MAX_COMMANDS);
	const id = label(turn.id ?? turnId ?? "(unknown)");
	const status = turn.status === undefined || turn.status === null
		? null : label(turn.status);
	return { turnId: turn.id === undefined || turn.id === null
	                 ? (turnId === undefined || turnId === null
	                    ? null : label(turnId))
	                 : label(turn.id),
	         status, itemTypes, agentMessages, commands, totals,
	         summary: clip(`turn ${id} ${status ?? "?"}: `
	                       + `${totals.items} items [${itemTypes.join(", ")}]`
	                       + (totals.commands > 0
	                          ? `; ${totals.commands} agent commands `
	                            + `[${commands.join("; ")}]`
	                          : "; NO agent command item"),
	                       MAX_SUMMARY_CHARS) };
}
