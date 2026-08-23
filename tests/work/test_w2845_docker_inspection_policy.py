"""W2845: the managed Docker inspection profile is an EXPLICIT reviewed
set of four read-only prefixes, and it stays one.

`work/records/2026/08/finding-v12-isolated-agent-workers/findings/
finding-v12-local-isolated-execution/findings/
finding-managed-docker-inspection-policy/` confirmed exactly
`docker version`, `docker info`, `docker inspect` and
`docker image inspect`. Unrestricted `docker` is not authorized: it can
mount host paths or the runtime socket, run privileged containers, and
mutate or destroy containers, images, networks and volumes outside the
filesystem sandbox. Mutable OCI lifecycle operations belong behind the
trusted Worker Manager's validated runtime adapter, which constrains
image identities, container names, mounts, privileges, output roots and
cleanup; a model receives that contract rather than a Docker shell.

The profile is written out in `tools/codex-event-bridge/src/exec_policy.mjs`
beside the managed Work workflow profile, and written out again here.
These cases do not make one follow the other; they make a divergence
LOUD, so widening the ruled capability stays a decision somebody makes.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
EXEC_POLICY = os.path.join(REPO, "tools", "codex-event-bridge", "src",
                           "exec_policy.mjs")

# The confirmed profile, in the ruled order. Reading it from the module
# under test would make every case below tautological.
INSPECTIONS = (
	("docker", "version"),
	("docker", "info"),
	("docker", "inspect"),
	("docker", "image", "inspect"),
)

# Representative capability the ruling WITHHOLDS. A sample for these
# regressions, never the implementation's test: the module recognises
# the four ruled prefixes and treats everything else as outside the
# profile, so it maintains no list of forbidden Docker subcommands to
# keep in step with Docker's grammar.
WITHHELD = (
	("docker",),
	("docker", "image"),
	("docker", "run", "--privileged", "-v", "/:/host", "alpine"),
	("docker", "exec", "-it", "worker", "sh"),
	("docker", "rm", "-f", "worker"),
	("docker", "image", "rm", "worker:latest"),
	("docker", "build", "-t", "worker", "."),
	("docker", "pull", "alpine"),
	("docker", "volume", "prune", "-f"),
	("docker", "network", "create", "escape"),
	("docker", "system", "prune", "-af"),
	("docker", "cp", "worker:/etc/shadow", "."),
	# Read-only but UNRULED. The approver named four prefixes; a fifth
	# is a ruling to obtain, not one to make while implementing.
	("docker", "ps", "-a"),
	("docker", "logs", "worker"),
)

pytestmark = pytest.mark.skipif(
	shutil.which("node") is None,
	reason="the execution-policy generator is a Node module")

CODEX = shutil.which("codex")

# WHITESPACE THE INSTALLED EVALUATOR REFUSES, measured against
# `codex execpolicy check` rather than read off a grammar. Round 3 of the
# W2845 review: one TAB before the fourth generated rule made the audit
# report the file exact while Codex refused to parse it at all, so the
# dispatcher advertised inspection as provisioned with NONE of the four
# rules loaded — and the next managed inspection escalates for approval
# and is quarantined, which is the incident this Work exists to prevent.
#
# `tabs are not allowed` and `unexpected new indentation block` are the
# evaluator's own words. The oracle case below re-asks it, so a future
# Codex that accepted one of these would fail as a STALE fixture rather
# than leave the audit quietly wrong.
def _refused_whitespace():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	return {
		"tab before a rule": f"{head}\n\t{rules[3]}\n",
		"tab between operands":
			head + '\nprefix_rule(pattern=[\t"docker", "image", "inspect"], '
			'decision="allow")\n',
		"tab before the paren":
			head + '\nprefix_rule\t(pattern=["docker", "image", "inspect"], '
			'decision="allow")\n',
		"space-indented rule": f"{head}\n  {rules[3]}\n",
		"lone carriage return": f"{head}\r{rules[3]}\n",
		"form feed": f"{head}\n\f{rules[3]}\n",
		"non-breaking space": f"{head}\n\u00a0{rules[3]}\n",
	}


# Spellings the evaluator DOES load. Fail-closed must not become
# fail-blind: the operator's installed file is written in the first of
# them, and refusing the others would send somebody to regenerate a
# policy that was already correct.
def _accepted_whitespace():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	return {
		"exact generated": "\n".join(rules) + "\n",
		"no trailing newline": "\n".join(rules),
		"trailing spaces": "  \n".join(rules) + "  \n",
		"blank lines": "\n\n".join(rules) + "\n\n",
		"comment lines": "# installed by the operator\n" + "\n".join(rules) + "\n",
	}


# W2845 round 4: literal-only `prefix_rule` calls in shapes the scanner
# fully decomposes that the installed evaluator still REFUSES to load.
# The reviewer found three; probing the evaluator added the duplicate
# `decision` and established that the accepted decision domain is exactly
# `allow`, `prompt` and `forbidden`, case-sensitively.
#
# Same failure as the whitespace round and worth restating: Codex loads
# NOTHING from the file — including the four rules an operator installed
# correctly — while the preflight advertises inspection as provisioned.
def _refused_literals():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	whole = "\n".join(rules)
	return {
		"duplicate pattern operand":
			head + '\nprefix_rule(pattern=["docker"],\n'
			'            pattern=["docker", "image", "inspect"], '
			'decision="allow")\n',
		"duplicate decision operand":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect"], '
			'decision="allow", decision="allow")\n',
		"empty pattern":
			whole + '\nprefix_rule(pattern=[], decision="allow")\n',
		"empty pattern, positional":
			whole + '\nprefix_rule([], "allow")\n',
		"invalid decision":
			whole + '\nprefix_rule(pattern=["not-docker"], decision="deny")\n',
		"invalid decision, positional":
			whole + '\nprefix_rule(["not-docker"], "deny")\n',
		"invalid decision, wrong case":
			whole + '\nprefix_rule(pattern=["not-docker"], decision="Allow")\n',
	}


# Literal spellings the evaluator DOES load. The generator emits only
# `allow`, but refusing an operator's valid restriction — or an empty
# pattern ELEMENT, which is a different thing from an empty pattern —
# would be fail-blind in the direction round 1 warned about.
def _accepted_literals():
	whole = "\n".join(_allow(prefix) for prefix in INSPECTIONS)
	return {
		"decision prompt":
			whole + '\nprefix_rule(pattern=["not-docker"], decision="prompt")\n',
		"decision forbidden":
			whole + '\nprefix_rule(pattern=["not-docker"], decision="forbidden")\n',
		"empty string pattern element":
			whole + '\nprefix_rule(pattern=[""], decision="allow")\n',
	}


# W2845 round 5: EMPTY COMMA FIELDS. The scanner filtered away every empty
# field after splitting on top-level commas, on the reasoning that a
# trailing comma leaves an empty tail and is valid syntax. That is true of
# ONE empty tail and of nothing else, so an empty head field, an empty
# middle field or a second trailing comma reached the rest of the scanner
# as a well-formed rule while the evaluator refused the whole file with
# `unexpected symbol ','`.
#
# The positional spelling is included because it reaches the same
# evaluator; it was not in the report.
def _refused_comma_fields():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	return {
		"empty element mid list":
			head + '\nprefix_rule(pattern=["docker",, "image", "inspect"], '
			'decision="allow")\n',
		"empty element head list":
			head + '\nprefix_rule(pattern=[,"docker", "image", "inspect"], '
			'decision="allow")\n',
		"empty operand head call":
			head + '\nprefix_rule(, pattern=["docker", "image", "inspect"], '
			'decision="allow")\n',
		"empty operand mid call":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect"],, '
			'decision="allow")\n',
		"double trailing comma call":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect"], '
			'decision="allow",,)\n',
		"double trailing comma list":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect",,], '
			'decision="allow")\n',
		"empty operand mid, positional":
			head + '\nprefix_rule(["docker", "image", "inspect"],, "allow")\n',
	}


# The one empty field that IS valid syntax, in every place it can appear.
def _accepted_comma_fields():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	return {
		"trailing comma in the call":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect"], '
			'decision="allow",)\n',
		"trailing comma in the pattern list":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect",], '
			'decision="allow")\n',
		"trailing comma in both":
			head + '\nprefix_rule(pattern=["docker", "image", "inspect",], '
			'decision="allow",)\n',
		"trailing comma, positional":
			head + '\nprefix_rule(["docker", "image", "inspect"], "allow",)\n',
	}


# W2845 round 6: a TAB on an otherwise BLANK line. Round 3's own measured
# table recorded blank lines holding a tab as loadable, and the scanner then
# refused every `OTHER_WHITESPACE` character wherever it sat — so an exact
# generated policy with one tab-only blank line failed preflight while the
# evaluator loaded it and returned `allow`. Nothing hidden; a valid operator
# file rejected. That is the fail-BLIND direction this record has warned
# about since round 1.
#
# The tolerance is a property of the LINE, and it is exactly SPACE and TAB.
def _accepted_blank_lines():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	whole = "\n".join(rules)
	return {
		"tab-only blank line": head + "\n\t\n" + rules[3] + "\n",
		"space and tab mixed": head + "\n \t \n" + rules[3] + "\n",
		"tab-only line at end of file": whole + "\n\t\n",
		"tab-only last line, no final newline": whole + "\n\t",
		"tab inside a comment": whole + "\n#\tinstalled by the operator\n",
	}


# The same character, still refused, because the evaluator still refuses it.
def _refused_blank_lines():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3])
	return {
		"trailing tab after a rule": head + "\n" + rules[3] + "\t\n",
		"form feed on its own line": head + "\n\f\n" + rules[3] + "\n",
		"vertical tab on its own line": head + "\n\v\n" + rules[3] + "\n",
		"non-breaking space on its own line":
			head + "\n\u00a0\n" + rules[3] + "\n",
		"ideographic space on its own line":
			head + "\n\u3000\n" + rules[3] + "\n",
	}


# W2845 round 7: SPACE/TAB INDENTATION BEFORE A COMMENT. `readPolicy`
# reached OTHER_WHITESPACE before it reached `#`, so `<TAB># note` was
# consumed as unaccounted and the comment branch was never entered — while
# the evaluator loaded the same policy and returned allow. Round 6's "tab
# inside a comment" case put the tab AFTER the hash, so it never exercised
# the indentation, and the SPACE-indented spelling worked only because a
# space is accepted whitespace and fell through by accident.
def _accepted_indented_comments():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:2])
	tail = "\n".join(rules[2:])
	whole = "\n".join(rules)
	return {
		"tab-indented comment": head + "\n\t# operator note\n" + tail + "\n",
		"two tabs then comment": head + "\n\t\t# operator note\n" + tail + "\n",
		"space and tab mixed": head + "\n \t # operator note\n" + tail + "\n",
		"space-indented comment": head + "\n  # operator note\n" + tail + "\n",
		"tab-indented comment at end of file": whole + "\n\t# note\n",
		"tab-indented comment, no final newline": whole + "\n\t# note",
	}


# The same characters, still refused. The last entry is what says this is a
# LINE rule: a tab sharing a line with a rule is a tab in code.
def _refused_indentation():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:2])
	tail = "\n".join(rules[2:])
	return {
		"form feed before a comment": head + "\n\f# note\n" + tail + "\n",
		"vertical tab before a comment": head + "\n\v# note\n" + tail + "\n",
		"non-breaking space before a comment":
			head + "\n\u00a0# note\n" + tail + "\n",
		"tab-indented comment sharing a line with a rule":
			"\n".join(rules[:3]) + "\n" + rules[3] + "\t# note\n",
	}


# W2845 round 8: a COMMENT INSIDE the rule. The scanner knew a comment at
# the top level, indented, and trailing a complete rule — but not one inside
# a multi-line `prefix_rule(...)`, where `matchingParen` kept it and the
# splitter handed it to the operand reader. An exact rule the evaluator
# loads and honours became unaccounted and its prefix was reported MISSING.
#
# The correction MASKS comment spans rather than parsing them, which is what
# keeps the review's other constraint: comment punctuation stays inert
# because it never reaches the splitter at all.
def _comments_inside_a_rule():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	head = "\n".join(rules[:3]) + "\n"
	return {
		"after the open paren": head + (
			'prefix_rule(\n    # operator note inside the call\n'
			'    pattern=["docker", "image", "inspect"],\n'
			'    decision="allow",\n)\n'),
		"between operands": head + (
			'prefix_rule(\n    pattern=["docker", "image", "inspect"],\n'
			'    # why this one\n    decision="allow",\n)\n'),
		"carrying quotes, commas, brackets and parens": head + (
			'prefix_rule(\n    # it\'s "fine", [really], (yes)\n'
			'    pattern=["docker", "image", "inspect"],\n'
			'    decision="allow",\n)\n'),
		"trailing an operand line": head + (
			'prefix_rule(\n    pattern=["docker", "image", "inspect"],  # prefix\n'
			'    decision="allow",\n)\n'),
		"holding a TAB in its body": head + (
			'prefix_rule(\n    #\toperator note\n'
			'    pattern=["docker", "image", "inspect"],\n'
			'    decision="allow",\n)\n'),
	}


# A TAB before the `#` is a tab in CODE, and the evaluator refuses it whether
# or not a comment follows.
def _tab_indented_comment_inside_a_rule():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	return "\n".join(rules[:3]) + "\n" + (
		'prefix_rule(\n\t# operator note\n'
		'    pattern=["docker", "image", "inspect"],\n'
		'    decision="allow",\n)\n')


# W2845 round 9: ASTRAL TEXT IN A COMMENT. Round 8's mask initialised its
# output with a code-POINT spread while every scanner indexes by UTF-16 code
# UNITS, so one emoji made the two spaces diverge and a LATER valid rule was
# misclassified. Each fixture carries a later rule, which is what makes the
# drift observable at all.
def _astral_comments():
	rules = [_allow(prefix) for prefix in INSPECTIONS]
	whole = "\n".join(rules)
	head = "\n".join(rules[:3])
	later = 'prefix_rule(pattern=["not-docker", "later"], decision="allow")'
	return {
		"top-level comment":
			whole + "\n# note \U0001F600 here\n" + later + "\n",
		"in-rule comment":
			head + "\nprefix_rule(\n    # note \U0001F600 here\n"
			'    pattern=["docker", "image", "inspect"],\n'
			"    decision=\"allow\",\n)\n" + later + "\n",
		"trailing comment on an operand line":
			head + "\nprefix_rule(\n"
			'    pattern=["docker", "image", "inspect"],  # \U0001F600\n'
			"    decision=\"allow\",\n)\n" + later + "\n",
		"astral inside a string operand":
			whole + '\nprefix_rule(pattern=["not-docker\U0001F600"], '
			'decision="allow")\n',
	}


def _module_exports():
	"""The profile as the module actually defines it, read by importing
	it rather than by parsing source text."""
	# The path is EMBEDDED in the script: `node -e` puts extra arguments
	# at argv[1], which is exactly where a directly-invoked module sees
	# its own path — and this module has a CLI that would then run.
	script = (
		f'const m = await import({json.dumps(EXEC_POLICY)});'
		'process.stdout.write(JSON.stringify('
		'{inspections: m.DOCKER_INSPECTIONS, profile: m.INSPECTION_PROFILE, '
		'rules: m.inspectionRules()}));')
	proc = subprocess.run(
		["node", "--input-type=module", "-e", script],
		capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr
	return json.loads(proc.stdout)


def _audit(policy_text):
	"""`auditInspectionRules` over one policy text."""
	script = (
		f'const m = await import({json.dumps(EXEC_POLICY)});'
		'let text = ""; for await (const chunk of process.stdin) text += chunk;'
		'process.stdout.write(JSON.stringify(m.auditInspectionRules(text)));')
	proc = subprocess.run(
		["node", "--input-type=module", "-e", script],
		input=policy_text, capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr
	return json.loads(proc.stdout)


def _allow(argv):
	return (f'prefix_rule(pattern=[{", ".join(json.dumps(e) for e in argv)}], '
	        f'decision="allow")')


EXACT = "\n".join(_allow(prefix) for prefix in INSPECTIONS)


def test_the_module_publishes_exactly_the_confirmed_inspection_profile():
	exports = _module_exports()
	assert exports["profile"] == "managed-docker-inspection"
	assert tuple(tuple(prefix) for prefix in exports["inspections"]) \
		== INSPECTIONS, \
		"the ruled inspection set drifted from the confirmed boundary; " \
		"widening it is a ruling to obtain, not an implementation decision"
	# No ruled prefix is a prefix of another. One that were would make
	# the shorter rule silently authorize the longer one's siblings —
	# which is exactly why `docker image` alone is refused below.
	for outer in INSPECTIONS:
		for inner in INSPECTIONS:
			if outer is inner:
				continue
			assert outer != inner[:len(outer)], \
				f"{' '.join(outer)} already authorizes {' '.join(inner)}"


def test_the_generator_emits_one_exact_rule_per_ruled_inspection():
	proc = subprocess.run(
		["node", EXEC_POLICY, "profile=managed-docker-inspection"],
		capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr
	rules = proc.stdout.splitlines()
	assert len(rules) == len(INSPECTIONS)
	pattern = re.compile(
		r'^prefix_rule\(pattern=\["docker"((?:, "[a-z]+")+)\], '
		r'decision="allow"\)$')
	emitted = []
	for rule in rules:
		match = pattern.match(rule)
		assert match, f"unexpected rule shape: {rule}"
		emitted.append(("docker", *re.findall(r'"([a-z]+)"', match.group(1))))
	# Order is part of the ruling: an operator diffing a regenerated file
	# against the record should see no reordering noise.
	assert tuple(emitted) == INSPECTIONS
	# The generator names no participant and no config. The capability
	# is the deployment host's, so it is emitted once for the whole
	# deployment rather than once per identity.
	assert "--participant" not in proc.stdout
	assert "baton" not in proc.stdout


def test_the_audit_withholds_unrestricted_and_mutable_docker():
	"""The distinction the ruling turns on. Every withheld shape leaves
	the preflight unsatisfied, and the two kinds stay apart because they
	need different corrections: a BROAD rule is removed, an EXTRA one is
	deleted and the capability reached through the Worker Manager."""
	assert _audit(EXACT)["satisfied"] is True
	for argv in WITHHELD:
		audit = _audit(f"{EXACT}\n{_allow(argv)}")
		assert audit["satisfied"] is False, \
			f"{' '.join(argv)} did not fail the inspection preflight"
		reported = ([entry["by"] for entry in audit["broad"]]
		            if audit["broad"] else audit["extra"])
		assert reported, f"{' '.join(argv)} was not reported at all"
	# `docker` and `docker image` are the BROAD shapes: they cover a
	# ruled inspection and every mutable command beside it.
	for argv in (("docker",), ("docker", "image")):
		audit = _audit(f"{EXACT}\n{_allow(argv)}")
		assert audit["broad"], f"{' '.join(argv)} was not reported as broad"
		assert audit["extra"] == []
	# Everything else covers no ruled inspection at all, so it is EXTRA.
	for argv in WITHHELD[2:]:
		audit = _audit(f"{EXACT}\n{_allow(argv)}")
		assert audit["broad"] == [], f"{' '.join(argv)} was reported as broad"
		assert audit["extra"] == [" ".join(argv)]


@pytest.mark.skipif(shutil.which("docker") is None,
                    reason="the ruled prefixes are checked against a real Docker")
def test_every_ruled_prefix_is_a_real_read_only_docker_command():
	"""A rule for a subcommand Docker does not have authorizes nothing
	and hides a typo behind a green preflight.

	This runs the ruled prefixes against the installed Docker. It says
	the profile names real read-only commands; it says NOTHING about the
	effective execution-policy boundary, which is established by the
	live matrix in `tools/codex-event-bridge/smoke/exact_policy_matrix.mjs`.
	"""
	for prefix in INSPECTIONS:
		proc = subprocess.run([*prefix, "--help"],
		                      capture_output=True, text=True, timeout=60)
		assert proc.returncode == 0, \
			f"{' '.join(prefix)} is not a Docker command: {proc.stderr[:200]}"
	# And the exact command whose approval request quarantined two
	# managed review turns produces the JSON the research step wanted.
	proc = subprocess.run(["docker", "version", "--format", "{{json .}}"],
	                      capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr[:400]
	assert "Client" in json.loads(proc.stdout)


def test_the_audit_refuses_whitespace_the_evaluator_cannot_parse():
	"""A file Codex cannot load authorizes nothing, including the four
	rules an operator did install. Reporting it as exact is the same
	parser/evaluator divergence as rounds 1 and 2, reached from the
	denial side instead of the privilege-escalation side."""
	for name, text in _refused_whitespace().items():
		audit = _audit(text)
		assert audit["satisfied"] is False, \
			f"the audit accepted evaluator-invalid whitespace: {name}"
		assert audit["unaccounted"], f"{name} was not reported as unaccounted"


def test_the_audit_still_reads_every_valid_space_and_newline_spelling():
	for name, text in _accepted_whitespace().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


def test_the_audit_refuses_literal_calls_the_evaluator_cannot_load():
	"""Round 4: the operand LITERALS. A repeated named operand was
	silently overwritten, and an empty pattern or an out-of-domain
	decision was returned as a parsed rule — so all three audited exact
	on a file Codex refuses outright."""
	for name, text in _refused_literals().items():
		audit = _audit(text)
		assert audit["satisfied"] is False, \
			f"the audit accepted an evaluator-invalid call: {name}"
		assert audit["unaccounted"], f"{name} was not reported as unaccounted"


def test_the_audit_still_reads_the_literals_the_evaluator_accepts():
	for name, text in _accepted_literals().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"
		# Read, and still not capability: only `allow` covers anything.
		assert audit["extra"] == [], name


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_literal_fixture(tmp_path):
	"""The oracle for round 4. The previous `decision="deny"` unit case
	asserted the audit's answer about a decision the evaluator rejects,
	so it could never have caught this; every fixture here is put in
	front of the evaluator first."""
	def check(text):
		policy = tmp_path / "literal.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _refused_literals().items():
		proc = check(text)
		assert proc.returncode != 0, \
			f"the evaluator now loads {name}; the fixture is stale, not the audit"
		assert "parse" in proc.stderr.lower(), (name, proc.stderr[:300])
	for name, text in _accepted_literals().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name


def test_the_audit_refuses_empty_comma_fields_the_evaluator_cannot_parse():
	"""Round 5: the PUNCTUATION. Only one empty tail is a valid trailing
	comma; an empty head or middle field and a second trailing comma are
	parse errors, so a file holding one authorizes nothing at all."""
	for name, text in _refused_comma_fields().items():
		audit = _audit(text)
		assert audit["satisfied"] is False, \
			f"the audit accepted an evaluator-invalid comma field: {name}"
		assert audit["unaccounted"], f"{name} was not reported as unaccounted"


def test_the_audit_still_reads_one_valid_trailing_comma():
	"""Fail-closed is not fail-blind, for the fifth time: an operator who
	wrote the approved rules with a trailing comma wrote the approved
	rules."""
	for name, text in _accepted_comma_fields().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


def test_the_audit_accounts_for_a_tab_only_blank_line():
	"""Round 6. A tab on an otherwise blank line is not a tab in code, and
	the evaluator has always loaded it. Refusing it made the dispatcher
	demand a regeneration that could not change what Codex authorizes."""
	for name, text in _accepted_blank_lines().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


def test_widening_the_blank_line_does_not_reopen_the_tab_defect():
	"""A tab is tolerated by the LINE being blank, never by being a tab."""
	for name, text in _refused_blank_lines().items():
		audit = _audit(text)
		assert audit["satisfied"] is False, \
			f"the audit accepted evaluator-invalid whitespace: {name}"
		assert audit["unaccounted"], f"{name} was not reported as unaccounted"
	# And round 3's own negatives still refuse.
	for name, text in _refused_whitespace().items():
		assert _audit(text)["satisfied"] is False, f"round 3's {name} is accepted again"


def test_the_audit_accounts_for_an_indented_comment():
	"""Round 7. The record has said since round 3 that a comment is
	accounted for wherever it sits, indented or trailing a rule; the
	SPACE-indented spelling only ever worked by accident."""
	for name, text in _accepted_indented_comments().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


def test_indentation_is_tolerated_before_a_comment_and_never_before_code():
	for name, text in _refused_indentation().items():
		audit = _audit(text)
		assert audit["satisfied"] is False, \
			f"the audit accepted evaluator-invalid whitespace: {name}"
		assert audit["unaccounted"], f"{name} was not reported as unaccounted"
	# Every earlier round's negatives still refuse: this widens what a
	# COMMENT line may hold and nothing else.
	for name, text in _refused_whitespace().items():
		assert _audit(text)["satisfied"] is False, f"round 3's {name} is accepted again"
	for name, text in _refused_blank_lines().items():
		assert _audit(text)["satisfied"] is False, f"round 6's {name} is accepted again"


def test_the_audit_accounts_for_a_comment_inside_a_rule():
	"""Round 8. Round 3 said a comment is accounted for wherever it sits, and
	inside a literal call is one of the places it sits."""
	for name, text in _comments_inside_a_rule().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["missing"] == [], \
			f"the rule's own prefix was reported missing: {name}"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


def test_comment_punctuation_stays_inert_and_a_tab_in_code_stays_code():
	"""The two boundaries the masking must not cross."""
	audit = _audit(_tab_indented_comment_inside_a_rule())
	assert audit["satisfied"] is False, \
		"a tab-indented comment INSIDE a rule was accepted"
	assert audit["unaccounted"]
	# A hash inside a STRING is part of the operand, not a comment.
	whole = "\n".join(_allow(prefix) for prefix in INSPECTIONS)
	data = whole + '\nprefix_rule(pattern=["not#docker"], decision="allow")\n'
	assert _audit(data)["unaccounted"] == []
	assert _audit(data)["satisfied"] is True


def test_astral_text_does_not_shift_the_comment_mask():
	"""Round 9. The mask must live in the same index space as the scanners
	that use it; a code-point array against code-unit offsets drifts after
	the first astral character."""
	for name, text in _astral_comments().items():
		audit = _audit(text)
		assert audit["unaccounted"] == [], f"{name} was reported as unaccounted"
		assert audit["missing"] == [], f"a rule went missing after: {name}"
		assert audit["satisfied"] is True, f"the audit refused a valid policy: {name}"


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_astral_fixture(tmp_path):
	def check(text):
		policy = tmp_path / "astral.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _astral_comments().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_in_rule_fixture(tmp_path):
	def check(text):
		policy = tmp_path / "inrule.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "image", "inspect", "node:24-slim"],
			capture_output=True, text=True, timeout=120)
	for name, text in _comments_inside_a_rule().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name
	stale = check(_tab_indented_comment_inside_a_rule())
	assert stale.returncode != 0, \
		"the evaluator now loads a tab-indented comment inside a rule; the " \
		"fixture is stale, not the audit"


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_indent_fixture(tmp_path):
	def check(text):
		policy = tmp_path / "indent.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _accepted_indented_comments().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name
	for name, text in _refused_indentation().items():
		proc = check(text)
		assert proc.returncode != 0, \
			f"the evaluator now loads {name}; the fixture is stale, not the audit"


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_blank_line_fixture(tmp_path):
	"""Both directions: a fixture the evaluator starts refusing would mean
	this widening had gone fail-blind, and one it starts accepting would
	make a negative case stale."""
	def check(text):
		policy = tmp_path / "blank.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _accepted_blank_lines().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name
	for name, text in _refused_blank_lines().items():
		proc = check(text)
		assert proc.returncode != 0, \
			f"the evaluator now loads {name}; the fixture is stale, not the audit"


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_comma_fixture(tmp_path):
	"""The oracle for round 5, asserted in both directions: a refused
	fixture the evaluator starts accepting is a stale fixture, and a
	trailing comma it starts refusing would mean the audit had gone
	fail-blind the other way."""
	def check(text):
		policy = tmp_path / "comma.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _refused_comma_fields().items():
		proc = check(text)
		assert proc.returncode != 0, \
			f"the evaluator now loads {name}; the fixture is stale, not the audit"
		assert "parse" in proc.stderr.lower(), (name, proc.stderr[:300])
	for name, text in _accepted_comma_fields().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name


@pytest.mark.skipif(CODEX is None,
                    reason="the evaluator is the oracle for what is parseable")
def test_the_installed_evaluator_agrees_about_every_whitespace_fixture(tmp_path):
	"""The oracle. `check` evaluates and does not execute, so no Docker
	command runs here."""
	def check(text):
		policy = tmp_path / "candidate.rules"
		policy.write_text(text, encoding="utf-8")
		return subprocess.run(
			[CODEX, "execpolicy", "check", "--rules", str(policy),
			 "docker", "version"],
			capture_output=True, text=True, timeout=120)
	for name, text in _refused_whitespace().items():
		proc = check(text)
		assert proc.returncode != 0, \
			f"the evaluator now loads {name}; the fixture is stale, not the audit"
		assert "parse" in proc.stderr.lower(), (name, proc.stderr[:300])
	for name, text in _accepted_whitespace().items():
		proc = check(text)
		assert proc.returncode == 0, \
			f"the evaluator refuses {name}, so the fixture is wrong: " \
			f"{proc.stderr[:300]}"
		assert json.loads(proc.stdout)["decision"] == "allow", name
