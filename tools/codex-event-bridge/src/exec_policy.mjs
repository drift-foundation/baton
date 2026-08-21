// W415: the deployment-owned exact command policy for managed turns.
//
// `work/records/2026/08/finding-managed-turn-approval-incidents/`.
//
// WHY THIS SHAPE, after three rejected ones. A managed turn's canonical
// Baton operations write to the coordination home, which is outside the
// workspace, so the sandbox refuses them and the turn escalates — and
// an escalation asks a human who is not in the conversation. Three
// candidate fixes were tried and rejected:
//
//   - `approvalPolicy: "never"` removes the prompt without making the
//     operation possible, and suppresses the approval request that this
//     Work's durable incident depends on;
//   - a writable coordination-home root makes the operation possible
//     and hands every shell command in the turn the power to rewrite or
//     delete `work.sqlite3` and `baton.json` (measured, not assumed);
//   - narrowing that root to a file or glob grants nothing at all
//     (also measured).
//
// The approver's ruling is an exact COMMAND policy instead. It is
// command-aware, which no filesystem grant is: a rule for
// `baton --config <cfg> --participant <p> claim` authorizes exactly
// that, and `rm work.sqlite3` matches nothing.
//
// TWO PROPERTIES MAKE IT SAFE, and both matter:
//
//   1. It is DEPLOYMENT-OWNED. This module generates and verifies the
//      rules; it never writes them. The operator installs them, because
//      a process that could grant itself authority has no boundary.
//   2. It is EXACT. Every rule names the installed executable, the
//      accepted config, the participant, and one ruled verb. The broad
//      form — the executable alone — is explicitly refused below, and
//      the live deployment currently has exactly that broad form.

import { readFileSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

// The one named profile. Everything in this module — the generator, the
// auditor, the refusals, and every regression — reads the capability
// from here, so there is exactly one place a capability decision lives.
export const POLICY_PROFILE = "managed-work-workflow";

// THE MANAGED WORK WORKFLOW PROFILE
// (`work/records/2026/08/finding-managed-turn-workflow-policy/`,
// confirmed 2026-08-21). One exact command rule for every public Work
// WORKFLOW mutation a managed agent may need while following repository
// and Baton policy.
//
// HOW THIS SET GOT HERE, because the history is the argument.
//
// The original ruling
// (`work/records/2026/08/finding-managed-turn-approval-incidents/`) was
// `claim`, `say`, `pass`, `close`. An earlier implementation of this
// list also carried `mark-seen`, on my judgement that a reviewer turn
// cannot discharge its reading obligation without it, and review round 4
// was RIGHT to reject that: an implementer does not widen a ruled
// capability while implementing it. That rejection said what to do
// instead — obtain and pin a ruling — and this is that ruling. The
// four-verb set is superseded AS TO THE VERB SET ONLY. Everything else
// it established stands unchanged and is implemented below:
// deployment-owned generation, exact binary/config/participant matching,
// broad-rule refusal, extra-verb refusal, and no raw access to
// `work.sqlite3`, `baton.json` or the coordination home.
//
// The concrete failure this profile corrects: a managed reviewer claimed
// W126, finished its review, and could not `mark-seen` its own
// discussion. The turn escalated for interactive approval, the
// non-interactive dispatcher refused, and the Work stayed
// authoritatively claimed by a runner whose turn was over — the exact
// stranding the claim boundary exists to prevent. A policy that permits
// enough mutation to TAKE Work but not enough to FINISH it is worse than
// one that permits neither.
//
// THIS IS AN EXPLICIT REVIEWED SET, NOT A DERIVED ONE. It is written out
// here rather than computed from the CLI's mutation registry, so a newly
// added public mutation is unauthorized until somebody deliberately adds
// it to this profile. `tests/work/test_w220_managed_workflow_policy.py`
// fails loudly when the registry and this profile drift apart; that is a
// prompt to make a decision, never an instruction to widen automatically.
export const RULED_VERBS = [
	"create", "accept", "respond", "dispose", "close", "block", "unblock",
	"mark-seen", "classify", "claim", "release", "prioritize", "pass",
	"heartbeat", "phase", "try", "extend", "report", "assess", "abandon",
	"revise", "start-thread", "say", "label", "unlabel", "bind", "poke",
	"poke-answer", "poke-cancel", "reroute",
];

// The public mutations this profile DELIBERATELY excludes, and why. A
// rule for any of these against the same executable, config and
// participant fails the preflight exactly like any other unruled verb;
// they are named here so the exclusion is a recorded decision rather
// than an omission somebody has to reconstruct.
export const EXCLUDED_VERBS = {
	// Deployment and configuration authority. A managed turn does not
	// get to accept a configuration generation or create an authority.
	deployment: ["activate", "regen"],
	// Runtime publication is the ADAPTER's, not the model's. These carry
	// no workflow authority, and a turn that could publish its own
	// runtime state could describe a runner that is not there.
	runtime: ["runtime-start", "runtime-state", "runtime-end",
	          "runtime-facts", "runtime-refresh"],
	// Incident publication is the DISPATCHER's and dismissal is the
	// action owner's. A managed turn that could file or dismiss its own
	// approval incident could erase the evidence of its own failure —
	// which is precisely how this defect surfaced.
	incident: ["incident", "dismiss"],
};

class ExecPolicyError extends Error {}

function quoted(value) { return JSON.stringify(String(value)); }

// One rule per ruled verb. A prefix rule authorizes a command whose
// argv STARTS with the pattern, so naming the verb is what keeps
// `claim` from also authorizing `regen` or `release`.
export function rulesFor({ binary, config, participant, verbs = RULED_VERBS }) {
	for (const [name, value] of Object.entries({ binary, config, participant })) {
		if (typeof value !== "string" || !value.trim()) {
			throw new ExecPolicyError(`exec policy needs a non-empty ${name}`);
		}
	}
	if (!binary.startsWith("/") || !config.startsWith("/")) {
		throw new ExecPolicyError(
			"exec policy needs the ABSOLUTE installed executable and accepted "
			+ "config; a relative path matches a different command depending on "
			+ "where the turn happens to be running");
	}
	return verbs.map((verb) => {
		const pattern = [binary, "--config", config, "--participant", participant, verb];
		return `prefix_rule(pattern=[${pattern.map(quoted).join(", ")}], decision="allow")`;
	});
}

// Parse just enough of the rules file to answer "is this exact command
// authorized". Deliberately not a general execpolicy evaluator: it reads
// `prefix_rule(pattern=[...], decision="...")` lines and ignores the
// rest, so an unfamiliar construct is invisible rather than
// misinterpreted as coverage.
export function parseRules(text) {
	const rules = [];
	const pattern = /prefix_rule\s*\(\s*pattern\s*=\s*\[([^\]]*)\]\s*,\s*decision\s*=\s*"([^"]+)"\s*\)/g;
	for (const match of text.matchAll(pattern)) {
		let argv;
		try { argv = JSON.parse(`[${match[1]}]`); }
		catch { continue; }
		if (!Array.isArray(argv) || argv.some((entry) => typeof entry !== "string")) continue;
		rules.push({ argv, decision: match[2] });
	}
	return rules;
}

// A rule COVERS a command when it is an allow rule and every element of
// its pattern matches the command's leading argv.
function covers(rule, command) {
	if (rule.decision !== "allow") return false;
	if (rule.argv.length > command.length) return false;
	return rule.argv.every((entry, index) => entry === command[index]);
}

// The audit an operator and the dispatcher both read.
//
// WHAT THIS DOES AND DOES NOT MEASURE (round-4 review). It reads ONE
// policy file that the deployment nominates. It does not and cannot
// observe the complete policy the app-server actually loaded: Codex may
// read other sources, and a deployment could point `execPolicyFile` at
// a pristine generated file while the server enforces something else.
//
// So this is a deployment PREFLIGHT on the nominated file, not a
// measurement of the effective boundary, and nothing here should be
// read as the latter. The effective boundary is established by the live
// matrix in `smoke/exact_policy_matrix.mjs`, which stands up an
// app-server whose policy contains only these rules and drives the
// positive and negative cases through it.
//
// A rule that is BROADER than the ruled command is reported as
// `broad` rather than as coverage. The live deployment's
// `prefix_rule(pattern=["…/bin/baton"], decision="allow")` authorizes
// every Baton verb this participant can reach, including `regen` and
// `release`, and calling that "covered" would be exactly the
// substitution this Work keeps rejecting.
export function auditRules(text, identity) {
	const rules = parseRules(text);
	const wanted = RULED_VERBS.map((verb) => ({
		verb,
		command: [identity.binary, "--config", identity.config,
		          "--participant", identity.participant, verb],
	}));
	const exact = new Set(rulesFor(identity));
	const missing = [];
	const broad = [];
	for (const { verb, command } of wanted) {
		const covering = rules.filter((rule) => covers(rule, command));
		if (!covering.length) { missing.push(verb); continue; }
		// EVERY broader covering rule is reported, even when an exact one
		// covers the same command.
		//
		// Round-6 review (of W415, when the ruled set was four verbs):
		// this used to record `broad` only when a ruled command had NO
		// exact rule, so that set's exact rules plus the retired
		// executable-only rule audited as satisfied — and that is
		// the most likely upgrade state, an operator adding the new rules
		// and forgetting to remove the old one. The dispatcher would have
		// started while the participant could still invoke every Baton
		// verb. A narrow rule does not cancel a broad one; both are
		// simply present, and the broad one still authorizes everything.
		const broader = covering.filter((rule) => rule.argv.length < command.length);
		if (broader.length) {
			broad.push({ verb, by: broader.map((rule) => rule.argv.join(" ")) });
		}
	}
	// REFUSED, per the Exact-set clarification pinned in FINDING.md
	// (2026-08-20), which the managed-workflow profile leaves in force:
	// the nominated participant policy IS the exact approved set, not
	// merely a file that happens to contain it. An allow rule for the
	// same executable, config and participant naming any other Baton
	// verb fails the preflight — including every verb the profile
	// deliberately excludes.
	//
	// I had left this advisory because refusing seemed to require a
	// second list of Baton's mutating verbs maintained here, which would
	// drift from the real grammar. The ruling dissolves that: no such
	// list is needed, because read-only commands need no
	// sandbox-crossing allow rule at all, and this policy file is
	// deliberately dedicated to the approved `managed-work-workflow`
	// profile — the thirty public Work WORKFLOW mutations in
	// `RULED_VERBS` and nothing else. So any verb outside that profile
	// is extra capability, whatever it does.
	//
	// The count matters here because this is the in-source explanation
	// of a security boundary. It said "the four managed mutations" until
	// W220 replaced that scope, and a maintainer reading the old
	// sentence could reasonably have concluded the other twenty-six
	// generated rules were unintended.
	//
	// Rules for OTHER configured participants are independent and stay
	// valid; this only ever looks at this participant's own prefix.
	const prefix = [identity.binary, "--config", identity.config,
	                "--participant", identity.participant];
	// Every allow rule that names a VERB after this participant's
	// prefix, whatever else it names after that.
	//
	// Round-1 W220 review: this used to require the pattern to be
	// EXACTLY one element longer than the prefix, and a prefix rule may
	// carry operands. So the thirty exact rules plus
	//
	//   prefix_rule(pattern=[…, "baton.codex", "regen",
	//                        "op-id=authorized-extra"], decision="allow")
	//
	// audited as satisfied while authorizing an excluded deployment
	// mutation — and the same hole admitted unknown and future verbs,
	// and operand-qualified reads. Narrower than a rule the ruling
	// never granted is still capability the ruling never granted.
	//
	// The test is on the VERB SLOT alone, because that is what the
	// ruling is about: a rule for a RULED verb carrying extra operands
	// authorizes a subset of a capability the profile already grants,
	// and an element in the verb slot that is not a ruled verb — an
	// excluded verb, an unknown one, or an operand where a verb should
	// be — is extra capability whatever follows it.
	const extra = [...new Set(rules
		.filter((rule) => rule.decision === "allow"
			&& rule.argv.length > prefix.length
			&& prefix.every((entry, index) => entry === rule.argv[index])
			&& !RULED_VERBS.includes(rule.argv[prefix.length]))
		.map((rule) => rule.argv[prefix.length]))];
	const present = [...exact].filter((line) => text.includes(line));
	// Broad coverage is NOT satisfaction. A rule naming the executable
	// alone authorizes every verb this participant can reach — `regen`,
	// `release`, anything — and accepting it would be the same
	// substitution of a broad capability for a narrow one that this Work
	// has rejected in several other forms.
	return { missing, broad, extra, exact: [...exact], present,
	         satisfied: !missing.length && !broad.length && !extra.length };
}

export function auditRulesFile(path, identity) {
	let text;
	try { text = readFileSync(path, "utf8"); }
	catch (error) {
		throw new ExecPolicyError(
			`the execution policy at ${path} is unreadable (${error.code ?? error.message}); `
			+ `a managed turn's canonical Baton operations are authorized by that `
			+ `file, so this dispatcher will not start without reading it`);
	}
	return auditRules(text, identity);
}

// Fail closed on the NOMINATED policy. A dispatcher whose managed turns
// cannot commit a canonical Baton operation is the defect this Work
// records, and it must not present itself as healthy while in that
// state. This is a preflight, not proof of the effective boundary — see
// `auditRules` above.
export function assertPolicyProvisioned(path, identity) {
	const audit = auditRulesFile(path, identity);
	if (audit.missing.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} does not authorize `
			+ `[${audit.missing.join(", ")}] for ${identity.participant}; a managed `
			+ `turn would escalate for interactive approval on those operations and `
			+ `the Work would sit unclaimed. Install these exact rules:\n`
			+ audit.exact.map((line) => `  ${line}`).join("\n"));
	}
	if (audit.broad.length) {
		const by = [...new Set(audit.broad.flatMap((entry) => entry.by))];
		const alsoExact = audit.present.length === audit.exact.length;
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} contains a BROADER rule `
			+ `[${by.join(" | ")}] covering `
			+ `[${audit.broad.map((entry) => entry.verb).join(", ")}] for `
			+ `${identity.participant}, which also authorizes every other verb `
			+ `this participant can reach`
			+ (alsoExact
				? ". The exact rules are present, and a narrow rule does not "
				  + "cancel a broad one — both are simply there. REMOVE the "
				  + "broad rule; this is the half-finished upgrade state."
				: ". The ruled capability is exact; install these rules and "
				  + "remove the broad one:\n"
				  + audit.exact.map((line) => `  ${line}`).join("\n")));
	}
	if (audit.extra.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} also authorizes `
			+ `[${audit.extra.join(", ")}] for ${identity.participant}. This file is `
			+ `dedicated to the approved '${POLICY_PROFILE}' set — exactly `
			+ `${RULED_VERBS.join(", ")} — and any other Baton verb for the same `
			+ `executable, config and participant is extra capability, including `
			+ `the deliberately excluded ${Object.values(EXCLUDED_VERBS).flat().join(", ")}. `
			+ `Remove those rules; read-only commands need no allow rule here. Rules `
			+ `for other participants are unaffected.`);
	}
	return audit;
}

export { ExecPolicyError };

// -- The INSTALLED generator: direct invocation -------------------------
//
// `work/records/2026/08/finding-deployed-exec-policy-helper/`. The
// d46ab1e release shipped a dispatcher template telling the operator to
// generate these rules with a path that exists only in the source
// checkout, and shipped no equivalent command. A standalone deployment
// could not follow its own instructions, which leaves an operator
// hand-authoring the security-sensitive rules this module exists to get
// right.
//
// The generator is THIS module rather than a second one beside it, so
// in any one checkout the code that emits the rules and the code that
// audits them is the same code. The release carries a byte-equal copy
// of this file, which is a DIFFERENT filesystem artifact from the
// module a source-run dispatcher imports; the deployer's byte-parity
// regression is what keeps the two from diverging.
//
// It PRINTS and nothing else — no file is created, overwritten, or
// installed. That is the same deployment-owned boundary property
// `assertPolicyProvisioned` depends on: a process that could grant
// itself authority has no boundary. Redirecting this output into the
// nominated policy file stays the operator's deliberate act.

export const USAGE =
	"usage: node exec_policy.mjs binary=/absolute/path/to/bin/baton "
	+ "config=/absolute/path/to/baton.json participant=team.member\n"
	+ "It prints the exact allow rules on stdout and installs nothing; "
	+ "redirect it into the deployment-owned policy file yourself.";

const OPERANDS = ["binary", "config", "participant"];

// Strict operands, because a generator that guessed would emit rules
// authorizing a command nobody asked for. Everything unrecognised,
// repeated, or absent is refused rather than defaulted, and the path
// and participant validation is `rulesFor`'s — this parses, it does not
// re-decide what a valid identity is.
export function identityFromOperands(argv) {
	const identity = {};
	for (const operand of argv) {
		const split = operand.indexOf("=");
		const name = split < 0 ? operand : operand.slice(0, split);
		if (!OPERANDS.includes(name)) {
			throw new ExecPolicyError(
				`unknown operand ${quoted(operand)}; this generator takes exactly `
				+ `${OPERANDS.join(", ")}`);
		}
		if (split < 0) {
			throw new ExecPolicyError(`operand ${name} needs a value: ${name}=...`);
		}
		if (Object.hasOwn(identity, name)) {
			throw new ExecPolicyError(
				`operand ${name} was given more than once; one generated policy `
				+ `names one executable, one accepted config and one participant`);
		}
		identity[name] = operand.slice(split + 1);
	}
	const missing = OPERANDS.filter((name) => !Object.hasOwn(identity, name));
	if (missing.length) {
		throw new ExecPolicyError(`missing operand(s): ${missing.join(", ")}`);
	}
	return identity;
}

export function generate(argv) {
	return `${rulesFor(identityFromOperands(argv)).join("\n")}\n`;
}

// Importing this module must stay side-effect-free: the dispatcher
// imports it during startup preflight, and a module that wrote to
// stdout on import would corrupt every consumer of that stream.
function invokedDirectly(entry) {
	if (!entry) return false;
	try { return realpathSync(entry) === realpathSync(fileURLToPath(import.meta.url)); }
	catch { return false; }
}

if (invokedDirectly(process.argv[1])) {
	try {
		process.stdout.write(generate(process.argv.slice(2)));
	} catch (error) {
		if (!(error instanceof ExecPolicyError)) throw error;
		process.stderr.write(`${error.message}\n${USAGE}\n`);
		process.exitCode = 1;
	}
}
