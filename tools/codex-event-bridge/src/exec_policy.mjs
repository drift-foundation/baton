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
	// W4615: deployment-global maintenance control. Draining suspends
	// every managed wake in the deployment until an explicit resume, so
	// a managed turn that could call it could suspend the stack it is
	// running in — and one that could `resume` could undo the operator's
	// maintenance boundary while the operator is acting on it. The
	// authority ruling (2026-08-22, obligation 4845) grants the
	// `dispatch` capability to `baton.slaw` alone; a managed
	// participant is not the holder, and an execution rule authorizing
	// the command would be a second, contradicting answer to who may.
	dispatch: ["drain", "resume"],
};

// THE MANAGED DOCKER INSPECTION PROFILE
// (`work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/
// finding-managed-docker-inspection-policy/`, approved 2026-08-22).
//
// A SECOND profile, and deliberately not more verbs on the first one.
// Everything above is one participant's authority over the coordination
// authority; this is host inspection, it names no participant and no
// config, and merging the two would mean a rule set that changes when
// an unrelated identity does.
//
// WHY IT EXISTS. Two managed `baton.codex` review turns for the v12 M2
// milestone were quarantined after requesting interactive approval for
// `docker version --format '{{json .}}'`. The dispatcher correctly
// denied the escalation, but restarting minted a fresh context without
// changing the execution policy, so the same research step failed
// again. A missing read-only capability strands Work exactly like a
// missing ruled verb does.
//
// WHY EXACTLY FOUR. The approver authorized read-only host inspection
// and nothing else. Unrestricted `docker` can mount host paths or the
// runtime socket, run privileged containers, and mutate or destroy
// containers, images, networks and volumes entirely outside the
// filesystem sandbox — so the executable-only prefix is refused below
// exactly like the executable-only Baton rule is. Mutable OCI lifecycle
// operations belong behind the trusted Worker Manager's validated
// runtime adapter, which constrains image identities, container names,
// mounts, privileges, output roots and cleanup; a model receives that
// contract rather than an arbitrary Docker shell.
//
// WHY THE PATTERN NAMES A BARE `docker` while every Baton rule names an
// ABSOLUTE executable. The two are invoked differently and a prefix
// rule matches the argv it is given. The dispatcher hands a managed
// turn the absolute installed Baton path, so naming it is free and
// exact; a turn inspecting the host types `docker version`, and a
// pattern of `/usr/bin/docker` would simply never match it. This is a
// real difference in what each rule pins — PATH decides which `docker`
// runs — and it is accepted because the capability behind it is
// read-only and the VERB SLOT is still exact. It is also the shape the
// operator installed by hand on 2026-08-22, which this generator
// exists to replace.
export const INSPECTION_PROFILE = "managed-docker-inspection";

export const DOCKER_INSPECTIONS = [
	["docker", "version"],
	["docker", "info"],
	["docker", "inspect"],
	["docker", "image", "inspect"],
];

class ExecPolicyError extends Error {}

function quoted(value) { return JSON.stringify(String(value)); }

// A prefix rule authorizes a command whose argv STARTS with the
// pattern. Both profiles emit this one shape, so a rule the generator
// prints and a rule the auditor accepts cannot drift in spelling.
function allowRule(pattern) {
	return `prefix_rule(pattern=[${pattern.map(quoted).join(", ")}], decision="allow")`;
}

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
	return verbs.map((verb) => allowRule(
		[binary, "--config", config, "--participant", participant, verb]));
}

// The inspection profile's rules. It takes NO operands: the capability
// is a property of the deployment host, not of any participant, so
// emitting it once per identity would put the same four lines in the
// file three times and invite somebody to "fix" one copy.
export function inspectionRules() {
	return DOCKER_INSPECTIONS.map(allowRule);
}

// Read the nominated policy file.
//
// SUPERSEDED 2026-08-22, and the superseded reasoning is worth keeping
// because it was confidently wrong. This used to be one regular
// expression matching `prefix_rule(pattern=[...], decision="...")`, and
// the comment above it said that being "deliberately not a general
// execpolicy evaluator" was SAFE — that an unfamiliar construct would be
// invisible rather than misinterpreted as coverage.
//
// Invisible IS misinterpreted as coverage. Round-1 W2845 review proved
// it against the installed evaluator: appending either
//
//     prefix_rule(decision="allow", pattern=["docker"])
//     prefix_rule(pattern=['docker'], decision='allow')
//
// to the four exact inspection rules makes `codex execpolicy check`
// authorize `docker run --privileged alpine`, while this module reported
// `satisfied: true`. Probing further, the policy language is Starlark: a
// variable, a string concatenation and a `for` loop all authorize the
// same thing. No regular expression can ever be complete against that.
//
// So the module stops pretending to parse a language and starts
// ACCOUNTING for a file. The nominated file is deployment-owned and
// GENERATED by this module; in the approved state it holds exactly the
// generated rules, blank lines and `#` comments. Anything this scanner
// cannot fully decompose into a `prefix_rule` over string literals is
// returned as UNACCOUNTED, and the preflights refuse on it. "I do not
// understand this file" and "this file is exact" are different answers,
// and only one of them was ever safe to give.

const RULE_NAME = "prefix_rule";

// One string literal, single- or double-quoted, or null if `text` is
// anything else at all — a variable, a concatenation, a number, a raw or
// triple-quoted string. Being strict here is what routes every cleverer
// spelling to UNACCOUNTED rather than to a half-understood rule.
//
// ESCAPES ARE ALMOST ENTIRELY REFUSED, and round 2 of the W2845 review is
// why. This used to treat every backslash sequence as syntax it
// understood, decoding `\n` and `\t` and otherwise dropping the backslash
// and copying the next character. That is not Starlark's semantics, and
// the reviewer proved the gap against the installed evaluator:
//
//     prefix_rule(pattern=["\x64ocker"], decision="allow")
//     prefix_rule(pattern=["\144ocker"], decision="allow")
//
// Starlark decodes both executables as `docker` and authorizes
// `docker run --privileged alpine`. This module decoded them as `x64ocker`
// and `144ocker`, matched no Docker rule, and reported the file exact. The
// same escape hides an absolute Baton executable from the workflow audit.
//
// The lesson is round 1's again: do not reimplement the language. The only
// escapes accepted are the ones this module's own generator can emit —
// `\\`, `\"` and `\'`, which are what `JSON.stringify` produces for a
// backslash or a quote inside an operand. Every other escape is refused,
// so `\x`, `\u`, octal and anything neither of us has thought of all land
// in UNACCOUNTED and fail the preflight closed.
//
// A DEPLOYMENT WHOSE PATHS NEED OTHER ESCAPES cannot be audited by this
// preflight, and that refusal is the honest answer: their exact evaluator
// semantics would have to be established against the oracle first, not
// guessed a second time.
const ACCEPTED_ESCAPES = { "\\": "\\", "\"": "\"", "'": "'" };

function stringLiteral(text) {
	const source = text.trim();
	const quote = source[0];
	if ((quote !== "\"" && quote !== "'") || source.length < 2) return null;
	let out = "";
	for (let at = 1; at < source.length; at += 1) {
		const character = source[at];
		// A LINE TERMINATOR ends a string literal in Starlark: the evaluator
		// refuses `"doc<newline>ker"` as an unfinished string literal rather
		// than reading a newline into the operand. Copying it here would be
		// this module reading a rule the evaluator never loaded.
		if (character === "\n" || character === "\r") return null;
		if (character === "\\") {
			const next = source[at + 1];
			if (next === undefined || !Object.hasOwn(ACCEPTED_ESCAPES, next)) return null;
			out += ACCEPTED_ESCAPES[next];
			at += 1;
			continue;
		}
		if (character === quote) return at === source.length - 1 ? out : null;
		out += character;
	}
	return null;
}

// Split on commas that are not inside a bracket or a string. Returns null
// when the comma-separated fields are not a shape the evaluator parses.
//
// EMPTY FIELDS ARE NOT ALL THE SAME, and round 5 of the W2845 review is
// why. This used to `filter` every empty field away, on the reasoning that
// a trailing comma is valid syntax and leaves an empty tail. That is true
// of ONE empty tail and of nothing else. The reviewer replaced the fourth
// inspection rule with
//
//     prefix_rule(pattern=["docker",, "image", "inspect"], decision="allow")
//     prefix_rule(pattern=[,"docker", "image", "inspect"], decision="allow")
//     prefix_rule(, pattern=["docker", "image", "inspect"], decision="allow")
//     prefix_rule(pattern=["docker", "image", "inspect"],, decision="allow")
//     prefix_rule(pattern=["docker", "image", "inspect"], decision="allow",,)
//
// and every one audited `satisfied=true` with nothing unaccounted, while
// the evaluator refused the whole file with
//
//     starlark error: error: Parse error: unexpected symbol ',',
//     expected expression
//
// so it loaded NO rule from it — including the three the operator had
// installed correctly. That is rounds 3 and 4's false-ready failure again:
// the dispatcher starts and advertises inspection as provisioned, and the
// next managed inspection escalates into a non-interactive dispatcher,
// is denied, and quarantines the context.
//
// MEASURED AGAINST codex-cli 0.149.0, not read off a grammar, because
// that reading has been wrong four times
// (`evidence/correction-round5-2026-08-22.txt`):
//
//   LOADS     one trailing comma in the call operand list, in the pattern
//             list, in both at once, and in the positional spelling
//   REFUSES   an empty head field, an empty middle field and a second
//             trailing comma, in the call and in the list alike, and an
//             empty middle field in the positional spelling
//
// So exactly one empty TAIL is dropped and any other empty field makes the
// whole construct unaccounted. `()` and `[]` hold no field at all and stay
// what they were: an empty operand list, which the empty-pattern rule of
// round 4 already refuses.
function splitTopLevel(text) {
	const parts = [];
	let depth = 0;
	let quote = null;
	let start = 0;
	for (let at = 0; at < text.length; at += 1) {
		const character = text[at];
		if (quote !== null) {
			if (character === "\\") { at += 1; continue; }
			if (character === quote) quote = null;
			continue;
		}
		if (character === "\"" || character === "'") { quote = character; continue; }
		if (character === "[" || character === "(") depth += 1;
		else if (character === "]" || character === ")") depth -= 1;
		else if (character === "," && depth === 0) {
			parts.push(text.slice(start, at));
			start = at + 1;
		}
	}
	parts.push(text.slice(start));
	// No comma at all and nothing between the brackets: zero fields.
	if (parts.length === 1) return parts[0].trim() === "" ? [] : parts;
	// The one valid trailing comma.
	if (parts[parts.length - 1].trim() === "") parts.pop();
	// Anything still empty is an empty head, an empty middle, or a second
	// trailing comma, and the evaluator refuses all three.
	if (parts.some((part) => part.trim() === "")) return null;
	return parts;
}

function stringList(text) {
	const source = text.trim();
	if (source[0] !== "[" || source[source.length - 1] !== "]") return null;
	const fields = splitTopLevel(source.slice(1, -1));
	if (fields === null) return null;
	const entries = fields.map(stringLiteral);
	return entries.some((entry) => entry === null) ? null : entries;
}

// THE OPERAND LITERALS ARE ACCOUNTED FOR TOO, and round 4 of the W2845
// review is why.
//
// Rounds 1, 2 and 3 corrected what this module read as SYNTAX. Round 4 is
// the same defect one layer further in: a call built entirely from string
// literals, in a shape this scanner fully decomposes, that the installed
// evaluator still refuses to load. The reviewer produced three, and
// probing the evaluator here produced a fourth:
//
//     prefix_rule(pattern=["docker"],
//                 pattern=["docker", "version"], decision="allow")
//     prefix_rule(pattern=["not-docker"], decision="allow", decision="allow")
//         -> starlark error: repeated named argument
//     prefix_rule(pattern=[], decision="allow")
//         -> invalid pattern element: pattern cannot be empty
//     prefix_rule(pattern=["not-docker"], decision="deny")
//         -> invalid decision: deny
//
// In all four the audit returned `missing=[] broad=[] extra=[]
// unaccounted=[] satisfied=true` while Codex loaded NO rule from the file
// — including the four inspection rules an operator had installed
// correctly. That is round 3's false-ready failure again: the dispatcher
// starts, advertises inspection as provisioned, and the next managed
// inspection escalates for approval into a non-interactive dispatcher
// that denies it and quarantines the context.
//
// THE DECISION DOMAIN WAS MEASURED, NOT DERIVED (codex-cli 0.149.0,
// `evidence/correction-round4-2026-08-22.txt`). The evaluator loads
// exactly `allow`, `prompt` and `forbidden`, case-sensitively, and
// refuses `deny`, `forbid`, `ask`, `reject`, `warn`, `allowed`, `Allow`,
// `ALLOW`, the empty string and anything else tried. Only `allow` is
// coverage, and only `allow` is what this generator emits; the other two
// are accepted because they LOAD, and refusing an operator's valid
// restriction would be fail-blind in the direction round 1 warned about.
// A decision outside the measured three is UNACCOUNTED — including a
// spelling a later Codex might add, which is the same stated limitation
// this module already carries for CRLF.
//
// An EMPTY STRING ELEMENT is a different question and stays accounted:
// `pattern=[""]` loads, and it covers nothing because no argv element
// equals the empty string. The evaluator's complaint is about an empty
// PATTERN, and that is what is refused here.
const EVALUATOR_DECISIONS = new Set(["allow", "prompt", "forbidden"]);

// Decompose one `prefix_rule(...)` operand list, in either keyword order,
// with either quote style, or positionally. Returns null when any operand
// is not a plain literal, when an operand is repeated, or when a literal
// falls outside the domain the installed evaluator accepts — each of
// which is the signal to treat the whole construct as unaccounted.
function decompose(body) {
	let argv = null;
	let decision = null;
	const named = new Set();
	const positional = [];
	const fields = splitTopLevel(body);
	if (fields === null) return null;
	for (const part of fields) {
		const at = part.indexOf("=");
		const name = at < 0 ? null : part.slice(0, at).trim();
		if (name !== null && /^[A-Za-z_][A-Za-z0-9_]*$/.test(name)
				&& part[at + 1] !== "=") {
			// A REPEATED named operand is a parse error for the whole file,
			// not a later value winning. This used to overwrite silently,
			// so a rule stating `pattern=["docker"]` and then
			// `pattern=["docker", "version"]` audited as the narrow one it
			// ended on while Codex loaded neither.
			if (named.has(name)) return null;
			named.add(name);
			const value = part.slice(at + 1);
			if (name === "pattern") argv = stringList(value);
			else if (name === "decision") decision = stringLiteral(value);
			else return null;
			continue;
		}
		positional.push(part);
	}
	// `prefix_rule(["docker"], "allow")` is valid and authorizes exactly
	// as much as the keyword form does.
	if (positional.length) {
		if (argv !== null || decision !== null || positional.length > 2) return null;
		argv = stringList(positional[0]);
		if (positional.length === 2) decision = stringLiteral(positional[1]);
	}
	if (argv === null || decision === null) return null;
	// The two literal domains, checked on BOTH spellings because the
	// positional form reaches the same evaluator.
	if (argv.length === 0) return null;
	if (!EVALUATOR_DECISIONS.has(decision)) return null;
	return { argv, decision };
}

// Blank out every COMMENT span, keeping the text's length and every other
// byte exactly.
//
// Round 8 of the W2845 review is why. The scanner recognised a comment at
// the top level, indented, and trailing a complete rule — but not one INSIDE
// a multi-line `prefix_rule(...)`. `matchingParen` kept it, `splitTopLevel`
// handed it to `decompose` as part of the next operand, and an exact rule
// the evaluator loads and honours became unaccounted. Round 3's boundary
// says a comment is accounted for "wherever it sits", and inside a call is
// one of the places it sits.
//
// MASKING RATHER THAN PARSING is the whole point. The review's constraint
// is that comment text must not become syntax: a body carrying quotes,
// commas, brackets or parentheses has to stay inert. Replacing the span
// with spaces means those characters never reach the splitter, the paren
// matcher or the operand reader at all — there is no interpretation to get
// wrong. Length is preserved so every offset, and therefore every quoted
// refusal fragment, still lines up with the original text.
//
// A `#` INSIDE A STRING IS DATA, and stays data: the walk tracks quote
// state with the same escape rule the rest of this module uses, so
// `pattern=["not#docker"]` is untouched.
//
// WHITESPACE IS NOT MASKED WITH IT. A tab BEFORE the `#` is still a tab in
// code and still refused — the evaluator refuses it too, measured this
// round — while a tab inside the comment BODY becomes a space here and is
// accepted, which is what the evaluator does.
function maskComments(text) {
	// `split("")` and NOT the spread, because the two disagree about what an
	// index is.
	//
	// Round 9 of the W2845 review: `[...text]` yields code POINTS while this
	// loop — and `matchingParen`, the whitespace accounting, the operand
	// reader and every offset into `text` — use UTF-16 code UNITS. One
	// astral character such as an emoji in a comment made the two spaces
	// diverge, so mask writes landed one element late, the joined mask
	// stopped lining up with the source, and a later VALID rule was
	// misclassified. The evaluator loaded those policies and authorized the
	// ruled inspection; only the audit refused them.
	//
	// The length invariant is what the rest of this module depends on, so it
	// is checked rather than assumed: a mask that is not the source's exact
	// length cannot be used to index the source.
	const out = text.split("");
	let quote = null;
	for (let at = 0; at < text.length; at += 1) {
		const character = text[at];
		if (quote !== null) {
			if (character === "\\") { at += 1; continue; }
			if (character === quote) quote = null;
			continue;
		}
		if (character === "\"" || character === "'") { quote = character; continue; }
		if (character !== "#") continue;
		while (at < text.length && text[at] !== "\n") {
			out[at] = " ";
			at += 1;
		}
	}
	const masked = out.join("");
	if (masked.length !== text.length) {
		throw new Error(
			`the comment mask is ${masked.length} code units against a source `
			+ `of ${text.length}; every scanner below indexes the source, so a `
			+ `mask that does not line up with it cannot be used`);
	}
	return masked;
}

// Find the `)` closing the `(` at `open`, ignoring brackets inside
// strings.
function matchingParen(text, open) {
	let depth = 0;
	let quote = null;
	for (let at = open; at < text.length; at += 1) {
		const character = text[at];
		if (quote !== null) {
			if (character === "\\") { at += 1; continue; }
			if (character === quote) quote = null;
			continue;
		}
		if (character === "\"" || character === "'") { quote = character; continue; }
		if (character === "(") depth += 1;
		else if (character === ")") {
			depth -= 1;
			if (depth === 0) return at;
		}
	}
	return -1;
}

// WHITESPACE IS ACCOUNTED FOR TOO, and round 3 of the W2845 review is why.
//
// The scanner below used to skip every character JavaScript calls `\s`.
// That was a THIRD reading of the language rather than an accounting of
// the file, and it was wrong in the same shape as rounds 1 and 2 — this
// time on the DENIAL side. The reviewer put one TAB before the fourth
// generated inspection rule. This module reported `satisfied: true`; the
// installed evaluator refused the whole file with
//
//     starlark error: error: Parse error: tabs are not allowed
//
// and made no authorization decision at all. A dispatcher starting on
// that file advertises inspection as provisioned while Codex cannot load
// one of the four rules, so the next managed inspection escalates for
// approval and is quarantined — the exact incident this Work exists to
// prevent, reached from the opposite direction.
//
// WHAT THE INSTALLED EVALUATOR DOES, measured against codex-cli 0.149.0
// rather than read off a grammar
// (`evidence/correction-round3-2026-08-22.txt`):
//
//   ACCEPTS   LF; spaces between tokens; trailing spaces; blank lines,
//             including ones holding a tab; CRLF; comment lines, indented
//             or not; a missing trailing newline
//   REFUSES   a TAB anywhere in code — line start, between tokens, even
//             between `prefix_rule` and its `(`; a statement indented by
//             SPACES ("unexpected new indentation block"); a lone CR, form
//             feed, vertical tab or NBSP ("invalid input"); a line
//             terminator inside a string literal ("unfinished string")
//
// Read the REFUSES row before the ACCEPTS one: those are files this
// module used to call exact and Codex will not load at all.
//
// So the accepted whitespace is the whitespace this module's own
// generator emits — SPACE and LF — and a top-level construct must BEGIN
// its line. That second clause is a refusal to read indentation, not
// another attempt to reproduce it: an indented statement is refused by
// the evaluator whether a tab or a space indents it, and this module has
// now been wrong three times about what it can safely interpret.
//
// It deliberately refuses one thing the evaluator would accept: CRLF line
// endings, which this generator never emits. Fail-closed there costs the
// operator one regeneration and a message that says so; the other
// direction cost two quarantined review turns.
const ACCEPTED_WHITESPACE = new Set([" ", "\n"]);

// Every whitespace character JavaScript recognises except those two.
// Written out rather than derived from `\s`, so the set an operator reads
// here is the set this module tests.
const OTHER_WHITESPACE =
	/[\t\v\f\r\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]/;
const OTHER_WHITESPACE_ALL = new RegExp(OTHER_WHITESPACE.source, "g");
const WHITESPACE_ESCAPES = { "\t": "\\t", "\v": "\\v", "\f": "\\f", "\r": "\\r" };

// Render a refused fragment so the character that refused it is VISIBLE.
// A TAB or a CR that vanishes into the operator's terminal is the one
// thing the refusal needs to name.
function visible(fragment) {
	return fragment.replace(OTHER_WHITESPACE_ALL, (character) =>
		WHITESPACE_ESCAPES[character]
		?? `\\u${character.codePointAt(0).toString(16).padStart(4, "0")}`);
}

// The whitespace a line may hold and still be BLANK. Exactly the two
// characters the evaluator tolerates there, measured rather than reasoned
// from `ACCEPTED_WHITESPACE` — a form feed is whitespace by every other
// definition and makes the evaluator refuse the whole file.
const BLANK_LINE_WHITESPACE = new Set([" ", "\t"]);

// Is the line starting at `from` blank? Returns the index just past its
// newline, or -1 when the line holds anything else — including a rule, a
// comment, or whitespace outside the tolerated pair.
function blankLineEnd(text, from) {
	const newline = text.indexOf("\n", from);
	const end = newline < 0 ? text.length : newline;
	for (let at = from; at < end; at += 1) {
		if (!BLANK_LINE_WHITESPACE.has(text[at])) return -1;
	}
	return newline < 0 ? text.length : newline + 1;
}

// Is the line starting at `from` INDENTED WHITESPACE followed by a comment?
// Returns the index just past its newline, or -1.
//
// Round 7 of the W2845 review is why this is separate from the blank-line
// rule. `readPolicy` reached `OTHER_WHITESPACE` before it reached `#`, so a
// line reading `<TAB># operator note` was consumed as unaccounted and the
// comment branch was never entered — while the installed evaluator loaded
// the exact same policy and returned `allow` for `docker version`. Round 6
// fixed the tab-only blank line and left this one, and round 6's own "tab
// inside a comment" case put the tab AFTER the `#`, so it never exercised
// the indentation.
//
// It also contradicted a rule this module already stated: round 3 measured
// indented comments as loadable and said in as many words that a comment is
// accounted for wherever it sits, "indented, or trailing a rule". The
// SPACE-indented spelling worked only because a space is accepted
// whitespace and fell through to the comment branch by accident.
//
// MEASURED AGAIN for this round against codex-cli 0.149.0
// (`evidence/correction-round7-2026-08-22.txt`):
//
//   LOADS     one tab, several tabs, or space and tab mixed before `#`;
//             the same at end of file with or without a final newline
//   REFUSES   a form feed, vertical tab or NBSP before `#`; a tab before a
//             RULE; a tab trailing a rule; and a tab-indented comment
//             sharing a line with a rule (`rule<TAB># note`), because that
//             tab is in code
//
// So the tolerance is the same SPACE and TAB, in the same position — the
// START of the line — and it is a property of the LINE for the same reason
// the blank rule is. A tab that appears after a statement is a tab in code
// however the line ends.
function commentLineEnd(text, from) {
	const newline = text.indexOf("\n", from);
	const end = newline < 0 ? text.length : newline;
	let at = from;
	while (at < end && BLANK_LINE_WHITESPACE.has(text[at])) at += 1;
	if (at >= end || text[at] !== "#") return -1;
	return newline < 0 ? text.length : newline + 1;
}

// The whitespace INSIDE one `prefix_rule(...)` construct. A tab between
// two operands is refused by the evaluator exactly like a tab at a line
// start, so a construct is readable only when every character outside its
// string literals is accepted whitespace or not whitespace at all. Inside
// a literal a tab is ordinary content and is left alone — the evaluator
// loads it, and a rule for `doc<tab>ker` authorizes `doc<tab>ker`.
function constructWhitespaceAccounted(construct) {
	let quote = null;
	for (let at = 0; at < construct.length; at += 1) {
		const character = construct[at];
		if (quote !== null) {
			if (character === "\\") { at += 1; continue; }
			if (character === quote) quote = null;
			continue;
		}
		if (character === "\"" || character === "'") { quote = character; continue; }
		if (OTHER_WHITESPACE.test(character)) return false;
	}
	return true;
}

// The scanner. Everything is either a blank line, a comment, a fully
// decomposed rule, or UNACCOUNTED.
export function readPolicy(text) {
	const rules = [];
	const unaccounted = [];
	// The same bytes with comment spans blanked, used for STRUCTURE only.
	// Every refusal still quotes the original.
	const code = maskComments(text);
	let at = 0;
	// Where the current line starts, so `at === lineFrom` is the question
	// "does this construct BEGIN its line" and the refusal can quote the
	// whole line rather than the tail the scanner happens to stand on.
	let lineFrom = 0;
	const note = (fragment) => {
		// `visible` runs BEFORE the trim, so a fragment that is nothing but a
		// stray carriage return is still reported rather than trimmed into
		// silence.
		const trimmed = visible(fragment).trim();
		if (trimmed !== "") unaccounted.push(trimmed.slice(0, 200));
	};
	// Report from `from` to the end of the current line and move past it.
	// Leading spaces are rendered rather than trimmed away: when the
	// INDENTATION is what refused the line, an operator shown a fragment
	// identical to the generated rule has been told nothing.
	const refuseLine = (from) => {
		const end = text.indexOf("\n", at);
		const line = text.slice(from, end < 0 ? text.length : end);
		note(line.replace(/^ +/, (run) => "\\x20".repeat(run.length)));
		at = end < 0 ? text.length : end + 1;
		lineFrom = at;
	};
	while (at < text.length) {
		const character = text[at];
		if (character === "\n") { at += 1; lineFrom = at; continue; }
		if (ACCEPTED_WHITESPACE.has(character)) { at += 1; continue; }
		// A TAB on an otherwise BLANK line is not a tab in code, and round
		// 6 of the W2845 review is why. This module sent every character in
		// `OTHER_WHITESPACE` straight to `refuseLine`, so an exact generated
		// policy with one tab-only blank line audited `unaccounted: ["\t"]`
		// and the dispatcher refused to start — while the installed
		// evaluator loaded that same file and returned `allow`. No
		// capability was hidden; the preflight simply demanded a
		// regeneration that could not change what Codex authorizes. That is
		// fail-BLIND in the other direction, against this record's own
		// stated boundary and against round 3's own accepted-spelling table,
		// which already recorded blank lines holding a tab as loadable.
		//
		// MEASURED AGAIN for this round against codex-cli 0.149.0, one
		// character per otherwise-blank line
		// (`evidence/correction-round6-2026-08-22.txt`):
		//
		//   LOADS     a line of TAB; a line of SPACE and TAB mixed; a
		//             tab-only line at end of file with or without a final
		//             newline
		//   REFUSES   a line of vertical tab, form feed, NBSP, U+1680,
		//             U+2000, U+2028, U+2029, U+202F, U+205F, U+3000 or
		//             U+FEFF — "invalid input", the whole file unloadable
		//
		// So the tolerance is exactly SPACE and TAB, and it is a property of
		// the LINE rather than of the character: the same tab before a rule,
		// between two operands, or trailing a rule on its own line is still
		// refused, because the evaluator refuses all three. Those three
		// negative cases are retained deliberately — widening this must not
		// reopen round 3.
		if (OTHER_WHITESPACE.test(character)) {
			// Two shapes tolerate SPACE/TAB at the start of a line, and
			// nothing else does: a line that is otherwise BLANK, and a line
			// that is otherwise a COMMENT.
			const blank = blankLineEnd(text, lineFrom);
			const past = blank >= 0 ? blank : commentLineEnd(text, lineFrom);
			if (past < 0) { refuseLine(at); continue; }
			at = past;
			lineFrom = past;
			continue;
		}
		// A COMMENT runs to the end of its line and is accounted for
		// wherever it sits — indented, or trailing a rule. Both were put in
		// front of the evaluator, which loads them; refusing an operator's
		// note beside the rule it explains would be fail-blind in the
		// direction round 1 warned about.
		if (character === "#") {
			const end = text.indexOf("\n", at);
			at = end < 0 ? text.length : end + 1;
			lineFrom = at;
			continue;
		}
		// A STATEMENT must BEGIN its line. Anything else is either indented,
		// which the evaluator refuses outright, or a second statement
		// sharing a line with the one already read.
		if (at !== lineFrom) { refuseLine(lineFrom); continue; }
		if (text.startsWith(RULE_NAME, at)) {
			const open = code.indexOf("(", at + RULE_NAME.length);
			const between = open < 0 ? "x" : code.slice(at + RULE_NAME.length, open);
			if (open >= 0 && between.trim() === "") {
				const close = matchingParen(code, open);
				if (close > 0) {
					const construct = text.slice(at, close + 1);
					const parsed = constructWhitespaceAccounted(code.slice(at, close + 1))
						? decompose(code.slice(open + 1, close))
						: null;
					if (parsed === null) note(construct);
					else rules.push(parsed);
					// A construct may span lines, and the next thing on its
					// LAST line is not indented by having been preceded by it.
					const lastBreak = construct.lastIndexOf("\n");
					if (lastBreak >= 0) lineFrom = at + lastBreak + 1;
					at = close + 1;
					continue;
				}
			}
		}
		// Anything else: report the line and move past it.
		refuseLine(at);
	}
	return { rules, unaccounted };
}

// The rules this module could fully decompose. Callers that need to know
// whether the file ALSO held something else read `readPolicy` directly;
// every assertion below does.
export function parseRules(text) {
	return readPolicy(text).rules;
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
	const { rules, unaccounted } = readPolicy(text);
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
	// UNACCOUNTED content is the round-1 W2845 correction, and it applies to
	// this profile too: the hole the review demonstrated with a reversed
	// keyword order on a `docker` rule is the same hole for a reversed
	// keyword order on the executable-only BATON rule. A file this module
	// cannot fully read is not one it may call exact.
	// Broad coverage is NOT satisfaction. A rule naming the executable
	// alone authorizes every verb this participant can reach — `regen`,
	// `release`, anything — and accepting it would be the same
	// substitution of a broad capability for a narrow one that this Work
	// has rejected in several other forms.
	return { missing, broad, extra, unaccounted, exact: [...exact], present,
	         satisfied: !missing.length && !broad.length && !extra.length
	                    && !unaccounted.length };
}

function readPolicyFile(path) {
	try { return readFileSync(path, "utf8"); }
	catch (error) {
		throw new ExecPolicyError(
			`the execution policy at ${path} is unreadable (${error.code ?? error.message}); `
			+ `a managed turn's canonical Baton operations are authorized by that `
			+ `file, so this dispatcher will not start without reading it`);
	}
}

export function auditRulesFile(path, identity) {
	return auditRules(readPolicyFile(path), identity);
}

// A rule NAMES DOCKER when its executable slot is `docker` or any path
// ending in it. The audit below deliberately looks at more than the
// bare `docker` the profile emits: `/usr/bin/docker run` is capability
// the ruling never granted, and an auditor that only recognised the
// spelling it generates would report a policy carrying it as clean.
function namesDocker(argv) {
	const executable = argv[0] ?? "";
	return executable === "docker" || executable.endsWith("/docker");
}

// The Docker half of the same preflight, and the same three questions:
// is each ruled inspection authorized, is anything BROADER authorizing
// it, and does this file grant Docker capability outside the profile.
//
// It takes no identity. The four prefixes are the whole profile, so a
// docker-naming allow rule is within it when some ruled prefix is a
// prefix of that rule — `docker inspect --format '{{json .}}'` is a
// subset of a capability already granted — and outside it otherwise.
//
// The two ways to be wrong are kept apart because they need different
// corrections. `docker` or `docker image` alone is BROAD: it covers a
// ruled inspection AND every mutable command beside it, so the fix is
// to remove that rule. `docker run` is EXTRA: it covers no ruled
// inspection at all, so the fix is to delete it and reach the runtime
// through the Worker Manager adapter instead. No list of forbidden
// Docker subcommands is maintained here — the profile is the four
// prefixes, and anything else is outside it whatever it does, which is
// the same reasoning that made the Baton extra-verb test need no list
// of Baton's verbs.
export function auditInspectionRules(text) {
	const read = readPolicy(text);
	const rules = read.rules.filter((rule) => namesDocker(rule.argv));
	const within = (rule) => DOCKER_INSPECTIONS.some((command) =>
		command.every((entry, index) => entry === rule.argv[index]));
	const missing = [];
	const broad = [];
	for (const command of DOCKER_INSPECTIONS) {
		const covering = rules.filter((rule) => covers(rule, command));
		if (!covering.length) { missing.push(command.join(" ")); continue; }
		// EVERY broader covering rule is reported even when the exact one
		// is also present — the half-finished upgrade state the Baton
		// audit learned to catch in its round-6 review. A narrow rule
		// does not cancel a broad one; both are simply there.
		const broader = covering.filter((rule) => rule.argv.length < command.length);
		if (broader.length) {
			broad.push({ command: command.join(" "),
			             by: broader.map((rule) => rule.argv.join(" ")) });
		}
	}
	const extra = [...new Set(rules
		.filter((rule) => rule.decision === "allow" && !within(rule)
			&& !DOCKER_INSPECTIONS.some((command) => covers(rule, command)))
		.map((rule) => rule.argv.join(" ")))];
	// A construct this module could not fully decompose is reported rather
	// than ignored. Round-1 W2845 review: an unaccounted rule is how an
	// unrestricted `docker` gets past a preflight that only knows one
	// spelling, and the policy language is Starlark — a variable, a string
	// concatenation and a `for` loop all authorize.
	return { missing, broad, extra, unaccounted: read.unaccounted,
	         exact: inspectionRules(),
	         satisfied: !missing.length && !broad.length && !extra.length
	                    && !read.unaccounted.length };
}

export function auditInspectionRulesFile(path) {
	return auditInspectionRules(readPolicyFile(path));
}

// Fail closed on the NOMINATED policy. A dispatcher whose managed turns
// cannot commit a canonical Baton operation is the defect this Work
// records, and it must not present itself as healthy while in that
// state. This is a preflight, not proof of the effective boundary — see
// `auditRules` above.
export function assertPolicyProvisioned(path, identity) {
	const audit = auditRulesFile(path, identity);
	// UNACCOUNTED CONTENT IS REPORTED FIRST, and round 3 of the W2845
	// review is why. A file this module cannot fully read is a file whose
	// OTHER answers are not trustworthy either: the reviewer's tab-indented
	// rule reports as `missing`, and telling an operator to install a rule
	// their file already contains sends them to the wrong correction. It is
	// worse than useless where the evaluator refuses the whole file, since
	// then every rule is inert and only one of them looked wrong.
	if (audit.unaccounted.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} contains policy this `
			+ `preflight cannot account for:\n`
			+ audit.unaccounted.map((line) => `  ${line}`).join("\n")
			+ `\nThis file is DEPLOYMENT-OWNED and generated: in the approved `
			+ `state it holds exactly the generated rules, blank lines and '#' `
			+ `comments. The policy language is a full one — a variable, a string `
			+ `concatenation or a loop can authorize anything — so a construct `
			+ `this preflight cannot read fails closed rather than being treated `
			+ `as absent. REGENERATE the file rather than editing it.\n`
			+ `WHITESPACE COUNTS: the evaluator refuses a TAB anywhere in a rule `
			+ `and refuses an indented statement, so only the spaces and `
			+ `newlines this generator emits are accounted for. A refused `
			+ `character is shown above as an escape.\n`
			+ `THE OPERAND LITERALS COUNT TOO: a repeated 'pattern' or `
			+ `'decision', an empty pattern, and any decision other than `
			+ `'allow', 'prompt' or 'forbidden' are each refused by the `
			+ `evaluator, which then loads NO rule from this file — including `
			+ `the ones installed correctly.`);
	}
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

// Fail closed on the Docker inspection profile, for the same reason and
// on the same nominated file.
//
// This one is DEPLOYMENT-WIDE rather than per participant, so the
// dispatcher calls it once. A missing inspection is treated exactly
// like a missing ruled verb — not as an optional extra — because the
// failure it produces is identical: the turn escalates for interactive
// approval, the non-interactive dispatcher denies it, the context is
// quarantined, and the Work sits unclaimed. A deployment whose host has
// no Docker still installs these four rules; they authorize a command
// that then fails on its own terms, which is an honest error the model
// can read, rather than an approval request nobody is there to answer.
export function assertInspectionProvisioned(path) {
	const audit = auditInspectionRulesFile(path);
	const install = () => audit.exact.map((line) => `  ${line}`).join("\n");
	// UNACCOUNTED CONTENT IS REPORTED FIRST, and round 3 of the W2845
	// review is why. A file this module cannot fully read is a file whose
	// OTHER answers are not trustworthy either: the reviewer's tab-indented
	// rule reports as `missing`, and telling an operator to install a rule
	// their file already contains sends them to the wrong correction. It is
	// worse than useless where the evaluator refuses the whole file, since
	// then every rule is inert and only one of them looked wrong.
	if (audit.unaccounted.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} contains policy this `
			+ `preflight cannot account for:\n`
			+ audit.unaccounted.map((line) => `  ${line}`).join("\n")
			+ `\nThis file is DEPLOYMENT-OWNED and generated: in the approved `
			+ `state it holds exactly the generated rules, blank lines and '#' `
			+ `comments. The policy language is a full one — a variable, a string `
			+ `concatenation or a loop can authorize anything — so a construct `
			+ `this preflight cannot read fails closed rather than being treated `
			+ `as absent. REGENERATE the file rather than editing it.\n`
			+ `WHITESPACE COUNTS: the evaluator refuses a TAB anywhere in a rule `
			+ `and refuses an indented statement, so only the spaces and `
			+ `newlines this generator emits are accounted for. A refused `
			+ `character is shown above as an escape.\n`
			+ `THE OPERAND LITERALS COUNT TOO: a repeated 'pattern' or `
			+ `'decision', an empty pattern, and any decision other than `
			+ `'allow', 'prompt' or 'forbidden' are each refused by the `
			+ `evaluator, which then loads NO rule from this file — including `
			+ `the ones installed correctly.`);
	}
	if (audit.missing.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} does not authorize `
			+ `[${audit.missing.join(", ")}]; a managed turn inspecting the host `
			+ `would escalate for interactive approval on those commands and the `
			+ `Work would be quarantined unclaimed. Install these exact rules:\n`
			+ install());
	}
	if (audit.broad.length) {
		const by = [...new Set(audit.broad.flatMap((entry) => entry.by))];
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} contains a BROADER Docker `
			+ `rule [${by.join(" | ")}] covering `
			+ `[${audit.broad.map((entry) => entry.command).join(", ")}]. That rule `
			+ `also authorizes mutable Docker: mounting host paths or the runtime `
			+ `socket, privileged containers, and destroying containers, images, `
			+ `networks and volumes outside the filesystem sandbox. A narrow rule `
			+ `does not cancel a broad one — REMOVE it, and keep only:\n`
			+ install());
	}
	if (audit.extra.length) {
		throw new ExecPolicyError(
			`the nominated execution policy at ${path} also authorizes `
			+ `[${audit.extra.join(" | ")}]. This file is dedicated to the approved `
			+ `'${INSPECTION_PROFILE}' set — exactly `
			+ `${DOCKER_INSPECTIONS.map((command) => command.join(" ")).join(", ")} — `
			+ `and any other Docker command is extra capability. Mutable OCI `
			+ `lifecycle operations belong behind the trusted Worker Manager's `
			+ `validated runtime adapter, not a model-issued Docker command; remove `
			+ `those rules.`);
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
	+ `       node exec_policy.mjs profile=${INSPECTION_PROFILE}\n`
	+ `The first form prints one participant's '${POLICY_PROFILE}' rules and is `
	+ "run once per configured participant. The second prints the "
	+ "deployment-wide read-only Docker inspection rules and is run once; it "
	+ "names no participant because the capability is the host's, not an "
	+ "identity's.\n"
	+ "Both print the exact allow rules on stdout and install nothing; "
	+ "redirect them into the deployment-owned policy file yourself.";

const OPERANDS = ["binary", "config", "participant"];

function splitOperand(operand) {
	const split = operand.indexOf("=");
	return split < 0
		? { name: operand, value: null }
		: { name: operand.slice(0, split), value: operand.slice(split + 1) };
}

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

// Which profile this invocation asks for, and its operands.
//
// `profile=` is optional and defaults to the workflow profile, so every
// invocation the release already documents keeps working unchanged. It
// is refused rather than ignored when it names something else, because
// a generator that fell back to a default here would print one
// profile's rules to an operator who asked for the other's — and the
// output is a security boundary somebody then installs.
export function requestFromOperands(argv) {
	const named = argv.map(splitOperand).filter((entry) => entry.name === "profile");
	if (named.length > 1) {
		throw new ExecPolicyError(
			"operand profile was given more than once; one invocation prints one "
			+ "profile, so run it once per profile and append");
	}
	if (named.length && named[0].value === null) {
		throw new ExecPolicyError("operand profile needs a value: profile=...");
	}
	const rest = argv.filter((operand) => splitOperand(operand).name !== "profile");
	const profile = named.length ? named[0].value : POLICY_PROFILE;
	if (profile === POLICY_PROFILE) {
		return { profile, identity: identityFromOperands(rest) };
	}
	if (profile === INSPECTION_PROFILE) {
		if (rest.length) {
			throw new ExecPolicyError(
				`the '${INSPECTION_PROFILE}' profile authorizes read-only host `
				+ `inspection and names no identity, so it takes no other operand; `
				+ `drop ${rest.join(", ")}`);
		}
		return { profile, identity: null };
	}
	throw new ExecPolicyError(
		`unknown profile ${quoted(profile)}; this generator prints `
		+ `'${POLICY_PROFILE}' from ${OPERANDS.join(", ")} and `
		+ `'${INSPECTION_PROFILE}' from profile=${INSPECTION_PROFILE} alone`);
}

export function generate(argv) {
	const request = requestFromOperands(argv);
	const rules = request.profile === INSPECTION_PROFILE
		? inspectionRules()
		: rulesFor(request.identity);
	return `${rules.join("\n")}\n`;
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
