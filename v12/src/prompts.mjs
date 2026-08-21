// The two turn inputs, and the one parser that reads structured answers
// back out of ACP prose.
//
// Both prompts state the boundary the container already enforces. That
// redundancy is deliberate: the kernel is what makes the boundary true,
// and telling the agent about it is what makes a refusal legible instead
// of looking like a malfunction.

import { INDEX_RULE } from "./fixture_check.mjs";

export function preClaimPrompt(offer) {
	const inputs = offer.inputs.map((input) =>
		`  - "${input.name}" (${input.type}): ${input.entries} file(s), `
		+ `${input.bytes} bytes, manifest digest ${input.digest}. `
		+ `It will be mounted READ-ONLY at ${input.mount}.`).join("\n");
	const outputs = offer.declared_outputs.map((output) =>
		`  - "${output.name}" (${output.type}) at ${output.path}`
		+ (output.entries
			? `, which must contain exactly: ${output.entries.join(", ")}`
			: "")).join("\n");
	return `You are being OFFERED a unit of work. You have not been assigned it, and you cannot start it from this turn.

This turn is for CONSENT ONLY, and it is running in a non-executing planning posture: you have no tool execution here. This container has no Baton executable, no Baton configuration and no Baton database, no copy of the Job's input, and nowhere to write a result. You cannot claim, publish, or begin the work from this turn even if you accept, and you should not try. Decide from the offer below alone.

The offer, in full:

  Work: ${offer.work}
  Offered to participant: ${offer.participant}
  Runtime attempt: ${offer.runtime_attempt}

  What the work asks for:
${offer.contract_human.split("\n").map((line) => `  ${line}`).join("\n")}

  Typed inputs you would receive:
${inputs}

  Declared outputs you would be expected to produce:
${outputs}

  Your single-use claim token (valid until ${offer.token.expires_at}):
  ${offer.token.value}

Decide whether to accept. Accept only if the contract is clear enough to execute deterministically and the declared inputs and outputs are sufficient for it; decline otherwise, and say plainly what is missing.

Reply with NOTHING but one fenced JSON block, exactly in this form:

\`\`\`json
{
  "envelope": "claim-intent",
  "version": "0-spike",
  "decision": "accept",
  "token": "<the claim token above, copied verbatim>",
  "work": "${offer.work}",
  "runtime_attempt": "${offer.runtime_attempt}",
  "reason": "<one sentence on why you accept or decline>"
}
\`\`\`

Use "decline" instead of "accept" if you are declining. The token must be copied exactly; a reply without it grants nothing and the work will simply be offered again.`;
}

export function executionPrompt(assignment, job) {
	return `You hold assignment generation ${assignment.generation} for Work ${assignment.work}. The claim was committed before this container was started, so this is genuinely yours to execute.

This container has no Baton executable, no Baton configuration and no Baton database. You cannot and need not report anything to Baton; the manager that started you collects your result and returns the work. Do not attempt any network coordination.

Your filesystem:
  ${job.input_mount}  READ-ONLY typed input, a directory. Its content is digest-verified before and after your turn; any attempt to modify it will fail and will invalidate the result.
  ${job.output_path}  the ONLY writable destination that counts as a result. It is a DIRECTORY, and it is the declared result: it must end up containing exactly ${job.entries.join(", ")} and nothing else. Anything you leave outside it is discarded, and anything extra inside it invalidates the result.
  /tmp   scratch, ephemeral, never collected.

The task:

${INDEX_RULE}

Read the input directory at ${job.input_mount} and write that JSON object to ${job.output_path}/${job.entries[0]}.

Do the work by reading the files, not by guessing. Say out loud, in at least one message before you finish, what you found in the input — that progress note is collected as an activity update and is part of the record.

When the file is written and you are satisfied it is correct, finish your reply with NOTHING but one fenced JSON block, exactly in this form:

\`\`\`json
{
  "envelope": "job.out",
  "version": "0-spike",
  "work": "${assignment.work}",
  "results": [{ "name": "${job.result_name}", "type": "directory", "path": "${job.output_path}" }],
  "summary": "<one sentence on what you produced>"
}
\`\`\``;
}

class ReplyError extends Error {}

// The agent answers in prose with a fenced block. Take the LAST fenced
// JSON block: a turn may reason about a shape before committing to one,
// and the final block is the commitment. A reply with no block at all is
// a refusal to answer in the contracted form, not a soft failure.
export function parseFencedJson(text) {
	const blocks = [...text.matchAll(/```(?:json)?\s*\n([\s\S]*?)```/g)];
	if (!blocks.length) {
		throw new ReplyError(
			"the agent's reply contained no fenced JSON block; the contracted "
			+ "reply format was not followed");
	}
	const last = blocks[blocks.length - 1][1];
	try { return JSON.parse(last); }
	catch (error) {
		throw new ReplyError(`the agent's final fenced block is not JSON: ${error.message}`);
	}
}

export { ReplyError };
