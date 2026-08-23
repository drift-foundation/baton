// W2845 round 1: the preflight must fail closed over every valid policy
// spelling, not just the one the generator emits.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/
// finding-managed-docker-inspection-policy/review-2026-08-22T05-48-15Z.md`.
//
// The review appended
//
//     prefix_rule(decision="allow", pattern=["docker"])
//     prefix_rule(pattern=['docker'], decision='allow')
//
// to the four exact inspection rules and showed that the installed
// evaluator authorized `docker run --privileged alpine` while the audit
// reported `satisfied: true`. The old parser was one regular expression
// that required `pattern` before `decision` and double quotes, and its
// comment claimed that ignoring an unfamiliar construct was SAFE.
//
// THESE CASES USE THE REAL EVALUATOR AS THE ORACLE. That is the whole
// point: the previous parser was wrong about what the language accepts,
// so a test written against my reading of the language would be wrong the
// same way. `codex execpolicy check` is asked whether each fixture really
// does authorize an unruled mutable command, and only then is the audit
// asked whether it refuses. When Codex is not installed the oracle cases
// skip and the pure-audit cases still run.

import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { auditInspectionRules, auditRules, inspectionRules, readPolicy,
         rulesFor, assertInspectionProvisioned, assertPolicyProvisioned }
	from "../src/exec_policy.mjs";

const dir = mkdtempSync("/tmp/w2845-syntax-");
let serial = 0;
const write = (text) => {
	const file = join(dir, `policy-${serial++}.rules`);
	writeFileSync(file, text);
	return file;
};

const IDENTITY = { binary: "/opt/baton/bin/baton",
	config: "/srv/baton/baton.json", participant: "baton.codex" };
const EXACT_INSPECTION = inspectionRules().join("\n");
const EXACT_BATON = rulesFor(IDENTITY).join("\n");

// Every spelling of an unrestricted `docker` rule this review turned up.
// The first two are the reviewer's; the rest came from probing the
// evaluator rather than from reading the old regular expression.
const UNRESTRICTED = [
	["canonical", 'prefix_rule(pattern=["docker"], decision="allow")'],
	["reversed keywords", 'prefix_rule(decision="allow", pattern=["docker"])'],
	["single quotes", "prefix_rule(pattern=['docker'], decision='allow')"],
	["mixed quotes", `prefix_rule(pattern=["docker"], decision='allow')`],
	["positional operands", 'prefix_rule(["docker"], "allow")'],
	["loose whitespace", 'prefix_rule(  pattern = [ "docker" ] ,  decision = "allow" , )'],
	// Indented with SPACES: Starlark refuses tabs outright, so a
	// tab-indented fixture would fail to parse rather than authorize — which
	// the oracle case below caught when this fixture used one.
	["multi-line", 'prefix_rule(\n    pattern=["docker"],\n    decision="allow",\n)'],
	// These are not `prefix_rule` calls this module can decompose at all.
	// The policy language is Starlark, so they authorize just as much.
	["variable indirection", 'D = ["docker"]\nprefix_rule(pattern=D, decision="allow")'],
	["string concatenation", 'prefix_rule(pattern=["doc" + "ker"], decision="allow")'],
	["a loop", 'for v in ["docker"]:\n    prefix_rule(pattern=[v], decision="allow")'],
	// Round 2: ordinary Starlark string ESCAPES. The old decoder dropped
	// the backslash and copied the next character, so `\x64ocker` read as
	// `x64ocker` — a rule for nothing, invisible to the Docker audit — while
	// the evaluator decoded it as `docker` and authorized a privileged
	// container. Every escape this module's own generator cannot emit is
	// now refused rather than interpreted a second time.
	["hex escape", 'prefix_rule(pattern=["\\x64ocker"], decision="allow")'],
	["unicode escape", 'prefix_rule(pattern=["\\u0064ocker"], decision="allow")'],
	["long unicode escape",
	 'prefix_rule(pattern=["\\U00000064ocker"], decision="allow")'],
	["octal escape", 'prefix_rule(pattern=["\\144ocker"], decision="allow")'],
	// And the string forms this module never emits at all.
	["raw string", 'prefix_rule(pattern=[r"docker"], decision="allow")'],
	["triple-quoted string", 'prefix_rule(pattern=["""docker"""], decision="allow")'],
];

const codex = spawnSync("codex", ["--version"], { encoding: "utf8" });
const oracleAvailable = codex.status === 0;

// Whether the INSTALLED evaluator can LOAD a policy at all. Round 3 turns
// on this and not on a decision: a file it refuses to parse authorizes
// nothing, so a preflight calling that file exact leaves the dispatcher
// advertising rules Codex never loaded.
function loads(file) {
	const proc = spawnSync("codex", ["execpolicy", "check", "--rules", file,
		"docker", "version"], { encoding: "utf8" });
	return { ok: proc.status === 0, error: `${proc.stderr}`.trim() };
}

// What the INSTALLED evaluator says about one command under one policy.
// `check` evaluates and does not execute, so nothing here runs Docker.
function evaluate(file, command) {
	const proc = spawnSync("codex", ["execpolicy", "check", "--rules", file, ...command],
		{ encoding: "utf8" });
	try {
		return JSON.parse(proc.stdout)?.decision ?? null;
	} catch {
		return null;
	}
}

test("W2845 R1: the audit refuses every spelling of unrestricted Docker", () => {
	// Pure audit, no oracle: this is the assertion that must hold on any
	// host, and it is the one the review found false.
	assert.equal(auditInspectionRules(`${EXACT_INSPECTION}\n`).satisfied, true,
		"the approved exact state must stay reachable");
	for (const [name, rule] of UNRESTRICTED) {
		const policy = `${EXACT_INSPECTION}\n${rule}\n`;
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		// It is reported as SOMETHING actionable — broad when the rule
		// decomposes, unaccounted when the construct does not.
		assert.ok(audit.broad.length || audit.extra.length || audit.unaccounted.length,
			`${name} was not reported at all`);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/BROADER Docker rule|cannot account for/, name);
	}
});

test("W2845 R1: the same hole is closed for the Baton workflow profile", () => {
	// The parser is shared, so the reversed-keyword executable-only BATON
	// rule was invisible for exactly the same reason. The review
	// demonstrated it on Docker; it was never only a Docker defect.
	assert.equal(auditRules(`${EXACT_BATON}\n`, IDENTITY).satisfied, true);
	for (const [name, spell] of [
		["reversed keywords",
		 `prefix_rule(decision="allow", pattern=["${IDENTITY.binary}"])`],
		["single quotes",
		 `prefix_rule(pattern=['${IDENTITY.binary}'], decision='allow')`],
		["positional operands", `prefix_rule(["${IDENTITY.binary}"], "allow")`],
		["variable indirection",
		 `B = ["${IDENTITY.binary}"]\nprefix_rule(pattern=B, decision="allow")`],
		// Round 2: the escape hides an absolute executable just as well as a
		// bare one, and the reviewer proved it on this profile too.
		["hex-escaped executable",
		 `prefix_rule(pattern=["\\x2fopt/baton/bin/baton"], decision="allow")`],
		["octal-escaped executable",
		 `prefix_rule(pattern=["\\057opt/baton/bin/baton"], decision="allow")`],
	]) {
		const policy = `${EXACT_BATON}\n${spell}\n`;
		assert.equal(auditRules(policy, IDENTITY).satisfied, false, name);
		assert.throws(() => assertPolicyProvisioned(write(policy), IDENTITY),
			/BROADER rule|cannot account for/, name);
		// The oracle half, for this profile too: each fixture really does
		// authorize a verb the workflow profile withholds.
		if (oracleAvailable) {
			assert.equal(
				evaluate(write(policy), [IDENTITY.binary, "unruled-verb"]), "allow",
				`${name} was expected to authorize an unruled Baton verb; if the `
				+ `evaluator no longer accepts this spelling the case is stale, `
				+ `not the audit`);
		}
	}
	// The approved state still denies it.
	if (oracleAvailable) {
		assert.notEqual(
			evaluate(write(`${EXACT_BATON}\n`), [IDENTITY.binary, "unruled-verb"]),
			"allow", "the exact workflow rules authorized an unruled verb");
	}
});

test("W2845 R1: a construct the preflight cannot read is refused, not ignored", () => {
	// The superseded reasoning said an unfamiliar construct would be
	// "invisible rather than misinterpreted as coverage". Invisible IS
	// misinterpreted as coverage, so the answer is now a refusal that names
	// what it could not read.
	for (const fragment of ['D = ["docker"]', 'load("other.rules", "x")',
	                        'prefix_rule(pattern=[SOMETHING], decision="allow")',
	                        'if True:\n    prefix_rule(pattern=["docker"], decision="allow")']) {
		const read = readPolicy(`${EXACT_INSPECTION}\n${fragment}\n`);
		assert.ok(read.unaccounted.length > 0, fragment);
		assert.equal(auditInspectionRules(`${EXACT_INSPECTION}\n${fragment}\n`).satisfied,
			false, fragment);
	}
	// The refusal says what to do about it.
	try {
		assertInspectionProvisioned(write(`${EXACT_INSPECTION}\nD = ["docker"]\n`));
		assert.fail("should have refused");
	} catch (error) {
		assert.match(error.message, /cannot account for/);
		assert.match(error.message, /REGENERATE the file/);
		assert.match(error.message, /D = \["docker"\]/, "the refusal does not quote it");
	}
});

test("W2845 R2: only the escapes this generator can emit are accepted", () => {
	// Fail-closed must not become fail-blind. `JSON.stringify` is what the
	// generator quotes with, and for an operand containing a backslash or a
	// quote it emits exactly `\\`, `\"` or `\'`. Those three decode the same
	// way here and in Starlark, so they stay readable; everything else is
	// refused rather than interpreted.
	const odd = { binary: "/opt/ba\\ton/bin/baton", config: "/srv/it's/baton.json",
		participant: "baton.codex" };
	const rules = rulesFor(odd).join("\n");
	assert.match(rules, /\\\\/, "the generator did not escape the backslash");
	const audit = auditRules(`${rules}\n`, odd);
	assert.deepEqual(audit.unaccounted, [],
		"the generator emitted a policy its own auditor cannot read");
	assert.equal(audit.satisfied, true);
	// A quote inside a participant round-trips too.
	const quoted = { ...IDENTITY, participant: `baton."odd"` };
	assert.equal(auditRules(`${rulesFor(quoted).join("\n")}\n`, quoted).satisfied, true);
});

test("W2845 R1: blank lines and comments are accounted for, not refused", () => {
	// A deployment-owned file holds the generated rules; an operator note
	// beside them is ordinary and must not fail the preflight.
	const annotated = `# installed 2026-08-22 by the operator\n\n${EXACT_INSPECTION}\n\n`
		+ `# regenerate with: node exec_policy.mjs profile=managed-docker-inspection\n`;
	const read = readPolicy(annotated);
	assert.deepEqual(read.unaccounted, []);
	assert.equal(read.rules.length, 4);
	assert.equal(assertInspectionProvisioned(write(annotated)).satisfied, true);
});

test("W2845 R1: the audit reads every spelling of the RULED prefixes too", () => {
	// Fail-closed must not become fail-blind: an operator who hand-wrote
	// the approved rules in another valid spelling has a correct policy,
	// and the preflight should say so rather than report them missing.
	const single = inspectionRules()
		.map((rule) => rule.replace(/"/g, "'")).join("\n");
	const audit = auditInspectionRules(`${single}\n`);
	assert.deepEqual(audit.missing, []);
	assert.deepEqual(audit.unaccounted, []);
	assert.equal(audit.satisfied, true);
});

test("W2845 R1: the installed evaluator agrees these policies are unrestricted",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		// The oracle half. Each fixture the audit refuses is shown to REALLY
		// authorize an unruled mutable command, so the refusals above are
		// protecting against something rather than being merely strict.
		//
		// `codex execpolicy check` evaluates and does not execute; Docker is
		// never invoked.
		const mutable = ["docker", "run", "--privileged", "alpine"];
		// First the control: the approved four DENY it.
		const exact = write(`${EXACT_INSPECTION}\n`);
		assert.notEqual(evaluate(exact, mutable), "allow",
			"the approved four rules authorized a privileged container");
		assert.equal(evaluate(exact, ["docker", "version", "--format", "{{json .}}"]),
			"allow", "the approved four rules did not authorize the ruled inspection");

		for (const [name, rule] of UNRESTRICTED) {
			const file = write(`${EXACT_INSPECTION}\n${rule}\n`);
			assert.equal(evaluate(file, mutable), "allow",
				`${name} was expected to authorize unrestricted Docker; if the `
				+ `evaluator no longer accepts this spelling the case is stale, `
				+ `not the audit`);
			// …and the audit refuses that same file.
			assert.equal(auditInspectionRules(`${EXACT_INSPECTION}\n${rule}\n`).satisfied,
				false, name);
		}
	});

// W2845 round 3: WHITESPACE. The reviewer put one TAB before the fourth
// generated rule; the audit reported `satisfied: true` and the installed
// evaluator refused the whole file with `Parse error: tabs are not
// allowed`, making no authorization decision at all.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T12-51-09Z.md`.
//
// This is rounds 1 and 2 again — a JavaScript reading of the language
// standing in for an accounting of the file — but on the DENIAL side. The
// dispatcher starts, advertises inspection as provisioned, and the next
// managed inspection escalates for approval and is quarantined: the exact
// incident W2845 exists to prevent.
//
// THE TABLE IS MEASURED, NOT READ. Each entry was put in front of
// `codex execpolicy check` first, and the oracle case below re-asserts
// that the evaluator still refuses to load it — so if a future Codex
// starts accepting one of these, the case fails as STALE rather than the
// audit being quietly wrong.
const FOUR = inspectionRules();
const EVALUATOR_REFUSES = [
	// The reviewer's exact reproduction.
	["tab before a rule", `${FOUR.slice(0, 3).join("\n")}\n\t${FOUR[3]}\n`],
	// "…including when it appears between tokens inside a rule rather than
	// only at line start."
	["tab between operands",
	 `${FOUR.slice(0, 3).join("\n")}\n`
	 + 'prefix_rule(pattern=[\t"docker", "image", "inspect"], decision="allow")\n'],
	["tab before the paren",
	 `${FOUR.slice(0, 3).join("\n")}\n`
	 + 'prefix_rule\t(pattern=["docker", "image", "inspect"], decision="allow")\n'],
	// Found while establishing the tab semantics, and the same defect: a
	// SPACE-indented statement is refused as an unexpected indentation
	// block. Fixing only the reported character would have left this one.
	["space-indented rule", `${FOUR.slice(0, 3).join("\n")}\n  ${FOUR[3]}\n`],
	// "invalid input" — the evaluator's lexer stops at each of these.
	["lone carriage return", `${FOUR.slice(0, 3).join("\n")}\r${FOUR[3]}\n`],
	["form feed", `${FOUR.slice(0, 3).join("\n")}\n\f${FOUR[3]}\n`],
	["vertical tab", `${FOUR.slice(0, 3).join("\n")}\n\v${FOUR[3]}\n`],
	["non-breaking space", `${FOUR.slice(0, 3).join("\n")}\n ${FOUR[3]}\n`],
	["non-breaking space inside a rule",
	 `${FOUR.slice(0, 3).join("\n")}\n`
	 + 'prefix_rule(pattern=[ "docker", "image", "inspect"], decision="allow")\n'],
	// A line terminator ENDS a string literal; the operand is unfinished,
	// not a name with a newline in it.
	["newline inside a string literal",
	 `${FOUR.slice(0, 3).join("\n")}\n`
	 + 'prefix_rule(pattern=["docker", "image\ninspect"], decision="allow")\n'],
];

test("W2845 R3: whitespace the evaluator refuses is unaccounted, not exact", () => {
	// The pure-audit half, which must hold on any host. This is the
	// assertion the review found false.
	for (const [name, policy] of EVALUATOR_REFUSES) {
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0,
			`${name} was not reported as unaccounted`);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/cannot account for/, name);
	}
	// The refusal shows the character that caused it. A tab the terminal
	// swallows tells an operator nothing, and the fragment would otherwise
	// be indistinguishable from the generated rule.
	try {
		assertInspectionProvisioned(
			write(`${FOUR.slice(0, 3).join("\n")}\n\t${FOUR[3]}\n`));
		assert.fail("should have refused");
	} catch (error) {
		assert.match(error.message, /\\t/, "the refusal does not show the tab");
		assert.match(error.message, /WHITESPACE COUNTS/);
		assert.match(error.message, /REGENERATE the file/);
	}
	// And an indented rule is shown as indented rather than trimmed into a
	// fragment that looks exactly like the approved one.
	assert.match(
		auditInspectionRules(`${FOUR.slice(0, 3).join("\n")}\n  ${FOUR[3]}\n`)
			.unaccounted.join("\n"),
		/\\x20\\x20prefix_rule/);
});

test("W2845 R3: the same whitespace hole is closed for the Baton profile", () => {
	// The reader is shared, so a tab-indented BATON rule was called exact
	// on a file Codex refuses to load — the workflow preflight would then
	// pass while the participant could commit no canonical operation at
	// all. It was never only a Docker defect, in any of the three rounds.
	const baton = rulesFor(IDENTITY);
	for (const [name, policy] of [
		["tab before a rule",
		 `${baton.slice(0, -1).join("\n")}\n\t${baton[baton.length - 1]}\n`],
		["space-indented rule",
		 `${baton.slice(0, -1).join("\n")}\n  ${baton[baton.length - 1]}\n`],
	]) {
		const audit = auditRules(policy, IDENTITY);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0, name);
		assert.throws(() => assertPolicyProvisioned(write(policy), IDENTITY),
			/cannot account for/, name);
		if (oracleAvailable) {
			assert.equal(loads(write(policy)).ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this whitespace the case is stale, not the audit`);
		}
	}
});

test("W2845 R3: valid space and newline spellings still audit exact", () => {
	// Fail-closed must not become fail-blind, for the third time. Every
	// spelling here was confirmed loadable by the installed evaluator, and
	// the operator's live 94-rule file is written in the first of them.
	for (const [name, policy] of [
		["exact generated", `${FOUR.join("\n")}\n`],
		["no trailing newline", FOUR.join("\n")],
		["trailing spaces", `${FOUR.join("  \n")}  \n`],
		["blank lines", `\n${FOUR.join("\n\n")}\n\n`],
		["blank line of spaces", `${FOUR.join("\n")}\n   \n`],
		["comment lines", `# installed by the operator\n${FOUR.join("\n")}\n`],
		// Both confirmed loadable by the evaluator: a comment is accounted
		// for wherever it sits, because refusing an operator's note beside
		// the rule it explains would be fail-blind.
		["an indented comment", `  # installed by the operator\n${FOUR.join("\n")}\n`],
		["a trailing comment",
		 `${FOUR.map((rule) => `${rule}  # ruled`).join("\n")}\n`],
		["spaces inside a rule",
		 FOUR.map((rule) => rule.replace(/, /g, " ,  ")).join("\n") + "\n"],
		["a rule across lines",
		 FOUR.slice(0, 3).join("\n")
		 + '\nprefix_rule(\n    pattern=["docker", "image", "inspect"],\n'
		 + '    decision="allow",\n)\n'],
	]) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [], name);
		assert.equal(audit.satisfied, true, `${name} was refused`);
		if (oracleAvailable) {
			assert.equal(loads(write(policy)).ok, true,
				`${name} is not loadable by the evaluator, so the fixture is wrong`);
		}
	}
});

test("W2845 R3: the installed evaluator cannot load these policies at all",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		// The oracle half, and the whole point of the round. Rounds 1 and 2
		// showed the evaluator ALLOWING what the audit called exact; this one
		// shows it refusing the file outright, which is worse in a quieter
		// way — nothing is authorized, including the four rules the operator
		// installed, and the preflight said the deployment was ready.
		for (const [name, policy] of EVALUATOR_REFUSES) {
			const { ok, error } = loads(write(policy));
			assert.equal(ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this whitespace the case is stale, not the audit`);
			assert.match(error, /Parse error|failed to parse policy/, name);
		}
		// The control: the approved file loads and still authorizes the ruled
		// inspection, so the refusals above are about the whitespace and not
		// about the rules.
		const exact = write(`${FOUR.join("\n")}\n`);
		assert.equal(loads(exact).ok, true);
		assert.equal(evaluate(exact, ["docker", "version"]), "allow");
	});

// W2845 round 4: THE OPERAND LITERALS. The reviewer built three
// `prefix_rule` calls entirely from string literals, in shapes this
// scanner fully decomposes, that the installed evaluator still refuses to
// load — a duplicate named operand, an empty pattern, and a decision
// outside the evaluator's domain. The audit returned `missing=[]
// broad=[] extra=[] unaccounted=[] satisfied=true` for all three.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T13-29-42Z.md`.
//
// It is round 3's failure in another semantic layer: Codex loads NOTHING
// from the nominated file — including the four inspection rules an
// operator installed correctly — while the dispatcher starts and
// advertises them as provisioned. The next managed inspection escalates
// for approval, the non-interactive dispatcher denies it, and the context
// is quarantined.
//
// MEASURED, NOT READ, like round 3's table. Probing the evaluator here
// added a fourth case the review did not have (a duplicate `decision`)
// and established the decision domain: it loads `allow`, `prompt` and
// `forbidden` and refuses `deny`, `forbid`, `ask`, `bogus`, `reject`,
// `warn`, `allowed`, `Allow`, `ALLOW` and the empty string.
const BATON = rulesFor(IDENTITY);
const withLast = (rules, replacement) =>
	`${rules.slice(0, -1).join("\n")}\n${replacement}\n`;

const EVALUATOR_INVALID_CALLS = [
	// The reviewer's exact reproduction: the duplicate silently overwrote,
	// so the audit read the rule it ended on.
	["duplicate pattern operand",
	 withLast(FOUR, 'prefix_rule(pattern=["docker"],\n'
	   + '            pattern=["docker", "image", "inspect"], decision="allow")')],
	// Found while establishing the semantics — the same parse error, and
	// the same overwrite, on the other operand.
	["duplicate decision operand",
	 withLast(FOUR, 'prefix_rule(pattern=["docker", "image", "inspect"], '
	   + 'decision="allow", decision="allow")')],
	["empty pattern", `${FOUR.join("\n")}\nprefix_rule(pattern=[], decision="allow")\n`],
	// The positional spelling reaches the same evaluator, so it has to
	// reach the same refusal.
	["empty pattern, positional", `${FOUR.join("\n")}\nprefix_rule([], "allow")\n`],
	["decision deny",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="deny")\n`],
	["decision forbid",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="forbid")\n`],
	["decision ask",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="ask")\n`],
	["decision bogus",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="bogus")\n`],
	// Case matters to the evaluator, and a decision domain read off a
	// grammar would probably have folded it.
	["decision Allow",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="Allow")\n`],
	["decision empty string",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker"], decision="")\n`],
	["decision deny, positional",
	 `${FOUR.join("\n")}\nprefix_rule(["not-docker"], "deny")\n`],
];

const EVALUATOR_INVALID_BATON = [
	["duplicate pattern operand",
	 withLast(BATON, `prefix_rule(pattern=["${IDENTITY.binary}"],\n`
	   + `            pattern=["${IDENTITY.binary}", "--config", `
	   + `"${IDENTITY.config}", "--participant", "${IDENTITY.participant}", `
	   + `"reroute"], decision="allow")`)],
	["empty pattern", `${BATON.join("\n")}\nprefix_rule(pattern=[], decision="allow")\n`],
	["decision deny",
	 `${BATON.join("\n")}\nprefix_rule(pattern=["/bin/true"], decision="deny")\n`],
];

test("W2845 R4: evaluator-invalid literal calls are unaccounted, not exact", () => {
	// The pure-audit half, which must hold on any host. This is the
	// assertion the fourth review found false.
	for (const [name, policy] of EVALUATOR_INVALID_CALLS) {
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0,
			`${name} was not reported as unaccounted`);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/cannot account for/, name);
	}
	// And the refusal quotes the call it could not account for, so an
	// operator is not told to go looking for a rule the file contains.
	try {
		assertInspectionProvisioned(write(
			`${FOUR.join("\n")}\nprefix_rule(pattern=[], decision="allow")\n`));
		assert.fail("should have refused");
	} catch (error) {
		assert.match(error.message, /prefix_rule\(pattern=\[\], decision="allow"\)/);
		assert.match(error.message, /REGENERATE the file/);
		assert.doesNotMatch(error.message, /does not authorize/,
			"a file the evaluator cannot load must not be reported as a "
			+ "missing rule; every rule in it is inert, not just one");
	}
});

test("W2845 R4: the same literal hole is closed for the Baton profile", () => {
	// The scanner is shared, so for the fourth time the workflow profile
	// carried it too: the workflow preflight would pass while Codex loaded
	// none of the participant's ruled verbs.
	for (const [name, policy] of EVALUATOR_INVALID_BATON) {
		const audit = auditRules(policy, IDENTITY);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0, name);
		assert.throws(() => assertPolicyProvisioned(write(policy), IDENTITY),
			/cannot account for/, name);
	}
});

test("W2845 R4: the decisions the evaluator ACCEPTS still audit exact", () => {
	// Fail-closed must not become fail-blind, for the fourth time. The
	// generator emits only `allow`, but `prompt` and `forbidden` load, so
	// an operator's valid restriction beside the ruled rules must be READ
	// — reported as not-coverage, never as a file to regenerate.
	for (const decision of ["prompt", "forbidden"]) {
		const policy = `${FOUR.join("\n")}\n`
			+ `prefix_rule(pattern=["not-docker"], decision="${decision}")\n`;
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [], decision);
		assert.equal(audit.satisfied, true, `${decision} was refused`);
		// Read, and still not capability.
		assert.deepEqual(audit.extra, [], decision);
	}
	// An EMPTY STRING ELEMENT is a different question from an empty
	// PATTERN: the evaluator loads it, and it covers nothing because no
	// argv element equals "". Refusing it would be fail-blind.
	const empties = `${FOUR.join("\n")}\nprefix_rule(pattern=[""], decision="allow")\n`;
	assert.deepEqual(auditInspectionRules(empties).unaccounted, []);
	assert.equal(auditInspectionRules(empties).satisfied, true);
});

test("W2845 R4: the installed evaluator cannot load these policies at all",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		// The oracle half, and the reason this round exists as its own case:
		// the previous unit coverage asserted the audit's answer about
		// `decision="deny"` without ever asking whether the evaluator
		// accepts that decision. It does not, so that case was asserting
		// behaviour on a file Codex will not load.
		for (const [name, policy] of [...EVALUATOR_INVALID_CALLS,
		                              ...EVALUATOR_INVALID_BATON]) {
			const { ok, error } = loads(write(policy));
			assert.equal(ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this call the case is stale, not the audit`);
			assert.match(error, /Parse error|failed to parse policy/, name);
		}
		// And the accepted domain is measured rather than assumed: these
		// three load, which is why the audit reads them.
		for (const decision of ["allow", "prompt", "forbidden"]) {
			assert.equal(loads(write(`${FOUR.join("\n")}\n`
				+ `prefix_rule(pattern=["not-docker"], decision="${decision}")\n`)).ok,
				true, `the evaluator no longer loads decision=${decision}`);
		}
		// The control: the approved file still loads and still authorizes the
		// ruled inspection, so the refusals above are about the literals.
		const exact = write(`${FOUR.join("\n")}\n`);
		assert.equal(loads(exact).ok, true);
		assert.equal(evaluate(exact, ["docker", "image", "inspect", "alpine"]),
			"allow");
	});


// W2845 round 5: EMPTY COMMA FIELDS. `splitTopLevel` filtered away every
// empty field on the reasoning that a trailing comma leaves an empty tail
// and is valid syntax. That is true of ONE empty tail and of nothing else.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T14-41-58Z.md`.
//
// The reviewer replaced the fourth inspection rule with five malformed
// forms; all five audited `missing=[] broad=[] extra=[] unaccounted=[]
// satisfied=true` while the evaluator refused the whole file with
// `unexpected symbol ','` and loaded none of its rules — rounds 3 and 4's
// false-ready failure again, one punctuation layer in.
//
// MEASURED against codex-cli 0.149.0, not read off a grammar:
//
//   LOADS     one trailing comma in the call, in the pattern list, in both
//             at once, and in the positional spelling
//   REFUSES   an empty head field, an empty middle field and a second
//             trailing comma, in the call and the list alike — and, found
//             here rather than in the report, an empty middle field in the
//             POSITIONAL spelling, which reaches the same evaluator
const EMPTY_COMMA_FIELDS = [
	["empty element mid list",
	 'prefix_rule(pattern=["docker",, "image", "inspect"], decision="allow")'],
	["empty element head list",
	 'prefix_rule(pattern=[,"docker", "image", "inspect"], decision="allow")'],
	["empty operand head call",
	 'prefix_rule(, pattern=["docker", "image", "inspect"], decision="allow")'],
	["empty operand mid call",
	 'prefix_rule(pattern=["docker", "image", "inspect"],, decision="allow")'],
	["double trailing comma call",
	 'prefix_rule(pattern=["docker", "image", "inspect"], decision="allow",,)'],
	["double trailing comma list",
	 'prefix_rule(pattern=["docker", "image", "inspect",,], decision="allow")'],
	// Not in the report. The positional spelling reaches the same
	// evaluator, so it has to reach the same refusal.
	["empty operand mid, positional",
	 'prefix_rule(["docker", "image", "inspect"],, "allow")'],
].map(([name, rule]) => [name, withLast(FOUR, rule)]);

const EMPTY_COMMA_FIELDS_BATON = [
	["empty element mid list",
	 `prefix_rule(pattern=["${IDENTITY.binary}",, "--config"], decision="allow")`],
	["empty operand head call",
	 `prefix_rule(, pattern=["${IDENTITY.binary}"], decision="allow")`],
	["double trailing comma call",
	 `prefix_rule(pattern=["${IDENTITY.binary}"], decision="allow",,)`],
].map(([name, rule]) => [name, `${BATON.join("\n")}\n${rule}\n`]);

// The one empty field that IS valid syntax, in every place it can appear.
// Fail-closed must not become fail-blind, for the fifth time: an operator
// who wrote the approved rules with a trailing comma wrote the approved
// rules.
const VALID_TRAILING_COMMA = [
	["call", 'prefix_rule(pattern=["docker", "image", "inspect"], decision="allow",)'],
	["pattern list",
	 'prefix_rule(pattern=["docker", "image", "inspect",], decision="allow")'],
	["both",
	 'prefix_rule(pattern=["docker", "image", "inspect",], decision="allow",)'],
	["positional", 'prefix_rule(["docker", "image", "inspect"], "allow",)'],
].map(([name, rule]) => [name, withLast(FOUR, rule)]);

test("W2845 R5: empty comma fields are unaccounted, not exact", () => {
	// The pure-audit half, which must hold on any host. This is the
	// assertion the fifth review found false.
	for (const [name, policy] of EMPTY_COMMA_FIELDS) {
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0,
			`${name} was not reported as unaccounted`);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/cannot account for/, name);
	}
});

test("W2845 R5: the same comma hole is closed for the Baton profile", () => {
	// The scanner is shared, so for the fifth time the workflow profile
	// carried it too.
	for (const [name, policy] of EMPTY_COMMA_FIELDS_BATON) {
		const audit = auditRules(policy, IDENTITY);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0, name);
		assert.throws(() => assertPolicyProvisioned(write(policy), IDENTITY),
			/cannot account for/, name);
	}
});

test("W2845 R5: one trailing comma is valid syntax and still audits exact", () => {
	for (const [name, policy] of VALID_TRAILING_COMMA) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [],
			`a valid trailing comma was reported as unaccounted: ${name}`);
		assert.equal(audit.satisfied, true,
			`the audit refused a valid trailing comma: ${name}`);
	}
	// And an empty operand list is still an empty operand list: `[]` holds
	// no field at all, so it stays round 4's empty-pattern refusal rather
	// than becoming a comma question.
	const empty = `${FOUR.join("\n")}\nprefix_rule(pattern=[], decision="allow")\n`;
	assert.equal(auditInspectionRules(empty).satisfied, false);
});

test("W2845 R5: the installed evaluator agrees about every comma fixture",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		// The oracle, for the fifth round. Both directions are asserted:
		// a fixture the evaluator starts accepting is a stale fixture, and
		// a valid trailing comma the evaluator starts refusing would mean
		// the audit is now fail-blind for the opposite reason.
		for (const [name, policy] of [...EMPTY_COMMA_FIELDS,
		                              ...EMPTY_COMMA_FIELDS_BATON]) {
			const { ok, error } = loads(write(policy));
			assert.equal(ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this comma the case is stale, not the audit`);
			assert.match(error, /unexpected symbol|Parse error|failed to parse policy/,
				name);
		}
		for (const [name, policy] of VALID_TRAILING_COMMA) {
			const file = write(policy);
			assert.equal(loads(file).ok, true,
				`the evaluator no longer loads a trailing comma in the ${name}`);
			assert.equal(evaluate(file, ["docker", "image", "inspect", "alpine"]),
				"allow", name);
		}
	});


// W2845 round 6: a TAB on an otherwise BLANK line.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T15-10-46Z.md`.
//
// Round 3's own accepted-spelling table recorded "blank lines, including
// ones holding a tab" as loadable, and then this module sent every
// character in `OTHER_WHITESPACE` straight to the line refusal. So an
// exact generated policy with one tab-only blank line audited
// `unaccounted: ["\t"] satisfied: false` while the installed evaluator
// loaded that same file and returned `allow`.
//
// Nothing was hidden — this is the OPPOSITE direction from rounds 1 to 5.
// The dispatcher refused to start on a valid operator file and demanded a
// regeneration that could not change what Codex authorizes. Fail-closed
// became fail-blind, which this record has warned about since round 1.
//
// MEASURED AGAIN, one character per otherwise-blank line. The tolerance is
// exactly SPACE and TAB; every other whitespace character makes the
// evaluator refuse the whole file even on a line of its own.
const BLANK_LINE_ACCEPTED = [
	["tab-only blank line", `${FOUR.slice(0, 3).join("\n")}\n\t\n${FOUR[3]}\n`],
	["space and tab mixed", `${FOUR.slice(0, 3).join("\n")}\n \t \n${FOUR[3]}\n`],
	["tab-only line at end of file", `${FOUR.join("\n")}\n\t\n`],
	["tab-only last line with no final newline", `${FOUR.join("\n")}\n\t`],
	["tab inside a comment", `${FOUR.join("\n")}\n#\tinstalled by the operator\n`],
	["several tab-only blank lines",
	 `${FOUR.slice(0, 2).join("\n")}\n\t\n\t\n${FOUR.slice(2).join("\n")}\n`],
];

// The same character, still refused, because the evaluator still refuses
// it: a tab is tolerated by the LINE being blank, never by being a tab.
const BLANK_LINE_STILL_REFUSED = [
	["trailing tab after a rule", `${FOUR.slice(0, 3).join("\n")}\n${FOUR[3]}\t\n`],
	["form feed on its own line", `${FOUR.slice(0, 3).join("\n")}\n\f\n${FOUR[3]}\n`],
	["vertical tab on its own line", `${FOUR.slice(0, 3).join("\n")}\n\v\n${FOUR[3]}\n`],
	["non-breaking space on its own line",
	 `${FOUR.slice(0, 3).join("\n")}\n \n${FOUR[3]}\n`],
	["ideographic space on its own line",
	 `${FOUR.slice(0, 3).join("\n")}\n　\n${FOUR[3]}\n`],
	["byte order mark on its own line",
	 `${FOUR.slice(0, 3).join("\n")}\n﻿\n${FOUR[3]}\n`],
];

test("W2845 R6: a tab-only blank line is accounted for, not refused", () => {
	for (const [name, policy] of BLANK_LINE_ACCEPTED) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [],
			`a valid policy was reported as unaccounted: ${name}`);
		assert.equal(audit.satisfied, true, `the audit refused ${name}`);
		assert.equal(assertInspectionProvisioned(write(policy)).satisfied, true, name);
	}
	// The Baton profile reads the same file through the same scanner.
	const baton = `${EXACT_BATON}\n\t\n`;
	assert.deepEqual(auditRules(baton, IDENTITY).unaccounted, []);
	assert.equal(auditRules(baton, IDENTITY).satisfied, true,
		"the workflow preflight refused a tab-only blank line");
	assert.equal(assertPolicyProvisioned(write(baton), IDENTITY).satisfied, true);
});

test("W2845 R6: widening it does not reopen round 3", () => {
	// A tab is tolerated by the LINE being blank, never by being a tab.
	// Round 3's negatives are re-asserted here rather than trusted: this is
	// the correction that could have reopened them.
	for (const [name, policy] of BLANK_LINE_STILL_REFUSED) {
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0, name);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/cannot account for/, name);
	}
	for (const [name, policy] of EVALUATOR_REFUSES) {
		assert.equal(auditInspectionRules(policy).satisfied, false,
			`round 3's ${name} is accepted again`);
	}
	const tabbedBaton = `${EXACT_BATON.split("\n").slice(0, -1).join("\n")}\n\t`
		+ `${EXACT_BATON.split("\n").at(-1)}\n`;
	assert.equal(auditRules(tabbedBaton, IDENTITY).satisfied, false,
		"a tab-indented Baton rule is accepted again");
});

test("W2845 R6: the installed evaluator agrees about every blank-line fixture",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		// Both directions, as in round 5. A fixture the evaluator starts
		// refusing would mean this widening had gone fail-blind; one it
		// starts accepting would make a negative case stale.
		for (const [name, policy] of BLANK_LINE_ACCEPTED) {
			const file = write(policy);
			assert.equal(loads(file).ok, true,
				`the evaluator does not load ${name}, so the fixture is wrong`);
			assert.equal(evaluate(file, ["docker", "image", "inspect", "alpine"]),
				"allow", name);
		}
		for (const [name, policy] of BLANK_LINE_STILL_REFUSED) {
			const { ok, error } = loads(write(policy));
			assert.equal(ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this whitespace the case is stale, not the audit`);
			assert.match(error, /Parse error|invalid input|failed to parse policy/, name);
		}
	});


// W2845 round 7: SPACE/TAB INDENTATION BEFORE A COMMENT.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T15-47-35Z.md`.
//
// `readPolicy` reached `OTHER_WHITESPACE` before it reached `#`, so a line
// reading `<TAB># operator note` was consumed as unaccounted and the
// comment branch was never entered — while the installed evaluator loaded
// the exact same policy and returned `allow`. Round 6's own "tab inside a
// comment" case put the tab AFTER the `#`, so it never exercised the
// indentation, and the SPACE-indented spelling worked only because a space
// is accepted whitespace and fell through by accident.
//
// It contradicted a rule this record already pinned in round 3: a comment
// is accounted for wherever it sits, indented or trailing a rule.
const INDENTED_COMMENTS = [
	["tab-indented comment", "\t# operator note"],
	["two tabs then comment", "\t\t# operator note"],
	["space and tab mixed then comment", " \t # operator note"],
	["space-indented comment", "  # operator note"],
].map(([name, line]) => [name,
	`${FOUR.slice(0, 2).join("\n")}\n${line}\n${FOUR.slice(2).join("\n")}\n`]);

const INDENTED_COMMENTS_AT_EOF = [
	["tab-indented comment at end of file", `${FOUR.join("\n")}\n\t# note\n`],
	["tab-indented comment, no final newline", `${FOUR.join("\n")}\n\t# note`],
];

// The same characters, still refused, because the evaluator still refuses
// them. The last row is the one that says this is a LINE rule: a tab
// sharing a line with a rule is a tab in code however the line ends.
const INDENT_STILL_REFUSED = [
	["form feed before a comment",
	 `${FOUR.slice(0, 2).join("\n")}\n\f# note\n${FOUR.slice(2).join("\n")}\n`],
	["vertical tab before a comment",
	 `${FOUR.slice(0, 2).join("\n")}\n\v# note\n${FOUR.slice(2).join("\n")}\n`],
	["non-breaking space before a comment",
	 `${FOUR.slice(0, 2).join("\n")}\n\u00a0# note\n${FOUR.slice(2).join("\n")}\n`],
	["tab-indented comment SHARING a line with a rule",
	 `${FOUR.slice(0, 3).join("\n")}\n${FOUR[3]}\t# note\n`],
];

test("W2845 R7: an indented comment is accounted for, not refused", () => {
	for (const [name, policy] of [...INDENTED_COMMENTS,
	                              ...INDENTED_COMMENTS_AT_EOF]) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [],
			`an evaluator-valid policy was reported as unaccounted: ${name}`);
		assert.equal(audit.satisfied, true, `the audit refused ${name}`);
		assert.equal(assertInspectionProvisioned(write(policy)).satisfied, true, name);
	}
	// The Baton profile reads the same file through the same scanner, which
	// is why this is the seventh round in which it carried the same hole.
	const baton = `${EXACT_BATON}\n\t# installed by the operator\n`;
	assert.deepEqual(auditRules(baton, IDENTITY).unaccounted, []);
	assert.equal(auditRules(baton, IDENTITY).satisfied, true,
		"the workflow preflight refused an indented comment");
	assert.equal(assertPolicyProvisioned(write(baton), IDENTITY).satisfied, true);
});

test("W2845 R7: indentation is tolerated before a COMMENT, never before code", () => {
	for (const [name, policy] of INDENT_STILL_REFUSED) {
		const audit = auditInspectionRules(policy);
		assert.equal(audit.satisfied, false, `${name} audited as satisfied`);
		assert.ok(audit.unaccounted.length > 0, name);
		assert.throws(() => assertInspectionProvisioned(write(policy)),
			/cannot account for/, name);
	}
	// And every earlier round's negatives still refuse: this correction
	// widens what a COMMENT line may hold and nothing else.
	for (const [name, policy] of EVALUATOR_REFUSES) {
		assert.equal(auditInspectionRules(policy).satisfied, false,
			`round 3's ${name} is accepted again`);
	}
	for (const [name, policy] of BLANK_LINE_STILL_REFUSED) {
		assert.equal(auditInspectionRules(policy).satisfied, false,
			`round 6's ${name} is accepted again`);
	}
	const tabbedBaton = `${EXACT_BATON.split("\n").slice(0, -1).join("\n")}\n\t`
		+ `${EXACT_BATON.split("\n").at(-1)}\n`;
	assert.equal(auditRules(tabbedBaton, IDENTITY).satisfied, false,
		"a tab-indented Baton rule is accepted again");
});

test("W2845 R7: the installed evaluator agrees about every indent fixture",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		for (const [name, policy] of [...INDENTED_COMMENTS,
		                              ...INDENTED_COMMENTS_AT_EOF]) {
			const file = write(policy);
			assert.equal(loads(file).ok, true,
				`the evaluator does not load ${name}, so the fixture is wrong`);
			assert.equal(evaluate(file, ["docker", "version"]), "allow", name);
		}
		for (const [name, policy] of INDENT_STILL_REFUSED) {
			const { ok, error } = loads(write(policy));
			assert.equal(ok, false,
				`${name} was expected to be unloadable; if the evaluator now `
				+ `accepts this whitespace the case is stale, not the audit`);
			assert.match(error, /Parse error|invalid input|failed to parse policy/,
				name);
		}
	});


// W2845 round 8: A COMMENT INSIDE THE RULE.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T16-46-17Z.md`.
//
// The scanner recognised a comment at the top level, indented, and trailing
// a complete rule — but not one INSIDE a multi-line `prefix_rule(...)`.
// `matchingParen` kept it and `splitTopLevel` handed it to `decompose` as
// part of the next operand, so an exact rule the evaluator loads and honours
// became unaccounted and its prefix was reported MISSING.
//
// The correction masks comment spans rather than parsing them, which is what
// keeps the review's other constraint: comment text must not become syntax.
// A body carrying quotes, commas, brackets or parentheses never reaches the
// splitter at all.
const INSIDE = (inner) => `${FOUR.slice(0, 3).join("\n")}\n${inner}\n`;

const COMMENTS_INSIDE_A_RULE = [
	["after the open paren", INSIDE(
		'prefix_rule(\n    # operator note inside the call\n'
		+ '    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)')],
	["between operands", INSIDE(
		'prefix_rule(\n    pattern=["docker", "image", "inspect"],\n'
		+ '    # why this one\n    decision="allow",\n)')],
	// The review's explicit constraint: comment PUNCTUATION stays inert.
	["carrying quotes, commas, brackets and parens", INSIDE(
		'prefix_rule(\n    # it\'s "fine", [really], (yes)\n'
		+ '    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)')],
	["trailing an operand line", INSIDE(
		'prefix_rule(\n    pattern=["docker", "image", "inspect"],  # the prefix\n'
		+ '    decision="allow",\n)')],
	["holding a TAB in its body", INSIDE(
		'prefix_rule(\n    #\toperator note\n'
		+ '    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)')],
	["on the closing line", INSIDE(
		'prefix_rule(\n    pattern=["docker", "image", "inspect"],\n'
		+ '    decision="allow",\n)  # ruled')],
];

test("W2845 R8: a comment inside a rule is accounted for, not refused", () => {
	for (const [name, policy] of COMMENTS_INSIDE_A_RULE) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [],
			`an evaluator-valid policy was reported as unaccounted: ${name}`);
		assert.deepEqual(audit.missing, [],
			`the rule's own prefix was reported missing: ${name}`);
		assert.equal(audit.satisfied, true, `the audit refused ${name}`);
		assert.equal(assertInspectionProvisioned(write(policy)).satisfied, true, name);
	}
	// The shared reader means the Baton profile carried it too — the eighth
	// round in which that has been true.
	const lines = EXACT_BATON.split("\n");
	const baton = `${lines.slice(0, -1).join("\n")}\n`
		+ lines.at(-1).replace("prefix_rule(", "prefix_rule(\n    # ruled verb\n    ")
		+ "\n";
	assert.deepEqual(auditRules(baton, IDENTITY).unaccounted, [], baton);
	assert.equal(auditRules(baton, IDENTITY).satisfied, true,
		"the workflow preflight refused a comment inside a rule");
});

test("W2845 R8: a hash inside a STRING is data, and a tab in code is still code",
	() => {
		// The two boundaries the masking must not cross. `#` inside a string
		// literal is part of the operand; a TAB before the `#` is a tab in
		// code, which the evaluator refuses whether or not a comment follows.
		const data = `${FOUR.join("\n")}\n`
			+ 'prefix_rule(pattern=["not#docker"], decision="allow")\n';
		assert.deepEqual(auditInspectionRules(data).unaccounted, []);
		assert.equal(auditInspectionRules(data).satisfied, true);
		// Read back through the scanner itself: the operand is ONE string
		// containing a hash, not a truncated one with a comment after it.
		assert.deepEqual(
			readPolicy(data).rules.at(-1).argv, ["not#docker"],
			"the hash-bearing operand was not read as one string");
		const tabbed = INSIDE(
			'prefix_rule(\n\t# operator note\n'
			+ '    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)');
		const audit = auditInspectionRules(tabbed);
		assert.equal(audit.satisfied, false,
			"a tab-indented comment INSIDE a rule was accepted");
		assert.ok(audit.unaccounted.length > 0);
		// And every earlier round's negatives still refuse.
		for (const [name, policy] of EVALUATOR_REFUSES) {
			assert.equal(auditInspectionRules(policy).satisfied, false,
				`round 3's ${name} is accepted again`);
		}
		for (const [name, policy] of INDENT_STILL_REFUSED) {
			assert.equal(auditInspectionRules(policy).satisfied, false,
				`round 7's ${name} is accepted again`);
		}
	});

test("W2845 R8: the installed evaluator agrees about every in-rule fixture",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		for (const [name, policy] of COMMENTS_INSIDE_A_RULE) {
			const file = write(policy);
			assert.equal(loads(file).ok, true,
				`the evaluator does not load ${name}, so the fixture is wrong`);
			assert.equal(evaluate(file, ["docker", "image", "inspect", "alpine"]),
				"allow", name);
		}
		// The tab-indented comment inside a rule is refused by the evaluator
		// too, which is why the audit still refuses it.
		const tabbed = INSIDE(
			'prefix_rule(\n\t# operator note\n'
			+ '    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)');
		const { ok, error } = loads(write(tabbed));
		assert.equal(ok, false,
			"the evaluator now loads a tab-indented comment inside a rule; the "
			+ "case is stale, not the audit");
		assert.match(error, /Parse error|tabs are not allowed|failed to parse policy/);
	});

// W2845 round 9: mask offsets must stay UTF-16 code-unit offsets. The source
// scanners index strings by code unit, but `[...text]` builds an array of code
// points. One astral character in an earlier comment then shifts every later
// mask assignment and turns a valid following rule into unaccounted text.
const ASTRAL_COMMENT_POLICIES = [
	["top-level comment", `${FOUR.join("\n")}\n# 😀 operator note\n`
		+ 'prefix_rule(pattern=["not-docker"], decision="allow")\n'],
	["comment inside a rule", `${FOUR.join("\n")}\n`
		+ 'prefix_rule(\n  # 😀 operator note\n'
		+ '  pattern=["not-docker"],\n  decision="allow",\n)\n'],
];

test("W2845 R9: astral text in a comment does not shift the policy mask", () => {
	for (const [name, policy] of ASTRAL_COMMENT_POLICIES) {
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.unaccounted, [], name);
		assert.equal(audit.satisfied, true, name);
	}
	const baton = `${EXACT_BATON}\n# 😀 operator note\n`;
	assert.deepEqual(auditRules(baton, IDENTITY).unaccounted, []);
	assert.equal(auditRules(baton, IDENTITY).satisfied, true);
});

test("W2845 R9: the evaluator loads the astral-comment fixtures",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
	for (const [name, policy] of ASTRAL_COMMENT_POLICIES) {
		const file = write(policy);
		assert.equal(loads(file).ok, true,
			`the evaluator does not load ${name}, so the fixture is wrong`);
		assert.equal(evaluate(file, ["docker", "version"]), "allow", name);
	}
});


// W2845 round 9: ASTRAL TEXT IN A COMMENT.
//
// `…/finding-managed-docker-inspection-policy/review-2026-08-22T17-42-34Z.md`.
//
// Round 8's mask initialised its output with `[...text]`, which yields code
// POINTS, while the loop and every scanner below index by UTF-16 code UNITS.
// One emoji in a comment made the two spaces diverge: mask writes landed one
// element late, the joined mask stopped lining up with the source, and a
// LATER valid rule was misclassified. The evaluator loaded those policies and
// authorized the ruled inspection; only the audit refused them.
//
// The later rule is what makes the drift observable, so every fixture here
// carries one.
const LATER = 'prefix_rule(pattern=["not-docker", "later"], decision="allow")';

const ASTRAL_COMMENTS = [
	["top-level comment", `${FOUR.join("\n")}\n# note \u{1F600} here\n${LATER}\n`],
	["in-rule comment",
	 `${FOUR.slice(0, 3).join("\n")}\nprefix_rule(\n    # note \u{1F600} here\n`
	 + `    pattern=["docker", "image", "inspect"],\n    decision="allow",\n)\n`
	 + `${LATER}\n`],
	["trailing comment on an operand line",
	 `${FOUR.slice(0, 3).join("\n")}\nprefix_rule(\n`
	 + `    pattern=["docker", "image", "inspect"],  # \u{1F600}\n`
	 + `    decision="allow",\n)\n${LATER}\n`],
	["several, at both levels",
	 `${FOUR.slice(0, 3).join("\n")}\n# \u{1F600}\u{1F600}\u{1F600}\nprefix_rule(\n`
	 + `    # \u{1F389} why\n    pattern=["docker", "image", "inspect"],\n`
	 + `    decision="allow",\n)\n${LATER}\n`],
	// Astral text OUTSIDE a comment is ordinary operand data and must be
	// read as itself, not shifted either.
	["astral inside a string operand",
	 `${FOUR.join("\n")}\nprefix_rule(pattern=["not-docker\u{1F600}"], decision="allow")\n`],
];

test("W2845 R9: astral text does not shift the mask off the source", () => {
	for (const [name, policy] of ASTRAL_COMMENTS) {
		const read = readPolicy(policy);
		assert.deepEqual(read.unaccounted, [],
			`an evaluator-valid policy was reported as unaccounted: ${name}`);
		// FIVE rules: the four inspections and the later one. A mask that
		// drifted lost or corrupted the rule after the astral character.
		assert.equal(read.rules.length, 5, name);
		const audit = auditInspectionRules(policy);
		assert.deepEqual(audit.missing, [], name);
		assert.equal(audit.satisfied, true, `the audit refused ${name}`);
		assert.equal(assertInspectionProvisioned(write(policy)).satisfied, true, name);
	}
	// The operand carrying the emoji is read as ONE string, unshifted.
	const data = readPolicy(ASTRAL_COMMENTS.at(-1)[1]);
	assert.deepEqual(data.rules.at(-1).argv, ["not-docker\u{1F600}"]);
	// The shared reader means the Baton profile carried it too — the ninth
	// round in which that has been true.
	const baton = `${EXACT_BATON}\n# operator note \u{1F600}\n`;
	assert.deepEqual(auditRules(baton, IDENTITY).unaccounted, []);
	assert.equal(auditRules(baton, IDENTITY).satisfied, true);
});

test("W2845 R9: the installed evaluator agrees about every astral fixture",
	{ skip: oracleAvailable ? false : "codex is not installed" }, () => {
		for (const [name, policy] of ASTRAL_COMMENTS) {
			const file = write(policy);
			assert.equal(loads(file).ok, true,
				`the evaluator does not load ${name}, so the fixture is wrong`);
			assert.equal(evaluate(file, ["docker", "version"]), "allow", name);
		}
	});
