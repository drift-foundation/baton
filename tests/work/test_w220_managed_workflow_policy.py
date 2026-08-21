"""W220: the managed-workflow execution-policy profile is an EXPLICIT
reviewed set, and it stays one.

`work/records/2026/08/finding-managed-turn-workflow-policy/` confirmed
one exact command rule per public Work WORKFLOW mutation, and named the
three groups it deliberately excludes. The profile is written out in
`tools/codex-event-bridge/src/exec_policy.mjs` rather than computed from
`baton_work.cli.MUTATIONS`, because a newly added public mutation must
stay unauthorized until somebody decides to authorize it.

That decision is what these cases protect. They do not make the profile
track the registry; they make a divergence LOUD, so the next person adding
a mutation has to place it in the profile or in the recorded exclusions.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
EXEC_POLICY = os.path.join(REPO, "tools", "codex-event-bridge", "src",
                           "exec_policy.mjs")

# The confirmed profile and its exclusions, written out here. Reading
# them from the module under test would make every case below tautological.
PROFILE = (
	"create", "accept", "respond", "dispose", "close", "block", "unblock",
	"mark-seen", "classify", "claim", "release", "prioritize", "pass",
	"heartbeat", "phase", "try", "extend", "report", "assess", "abandon",
	"revise", "start-thread", "say", "label", "unlabel", "bind", "poke",
	"poke-answer", "poke-cancel", "reroute",
)
EXCLUDED = {
	"deployment": ("activate", "regen"),
	"runtime": ("runtime-start", "runtime-state", "runtime-end",
	            "runtime-facts", "runtime-refresh"),
	"incident": ("incident", "dismiss"),
}

pytestmark = pytest.mark.skipif(
	__import__("shutil").which("node") is None,
	reason="the execution-policy generator is a Node module")


def _module_exports():
	"""RULED_VERBS and EXCLUDED_VERBS as the module actually defines
	them, read by importing it rather than by parsing source text."""
	# The path is EMBEDDED in the script: `node -e` puts extra arguments
	# at argv[1], which is exactly where a directly-invoked module sees
	# its own path — and this module has a CLI that would then run.
	script = (
		f'const m = await import({json.dumps(EXEC_POLICY)});'
		'process.stdout.write(JSON.stringify('
		'{ruled: m.RULED_VERBS, excluded: m.EXCLUDED_VERBS, '
		'profile: m.POLICY_PROFILE}));')
	proc = subprocess.run(
		["node", "--input-type=module", "-e", script],
		capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr
	return json.loads(proc.stdout)


def test_the_module_publishes_exactly_the_confirmed_profile():
	exports = _module_exports()
	assert exports["profile"] == "managed-work-workflow"
	assert tuple(exports["ruled"]) == PROFILE, \
		"the ruled capability drifted from the confirmed managed-workflow " \
		"profile; widening it is a ruling to obtain, not an implementation " \
		"decision"
	assert {key: tuple(value) for key, value
	        in exports["excluded"].items()} == EXCLUDED, \
		"the recorded exclusions drifted from the confirmed decision"
	# The two sets are disjoint, and neither carries a duplicate: an
	# exclusion that also appeared in the profile would authorize the
	# very thing it claims to withhold.
	flat = [verb for group in EXCLUDED.values() for verb in group]
	assert not set(PROFILE) & set(flat)
	assert len(set(PROFILE)) == len(PROFILE)
	assert len(set(flat)) == len(flat)


def test_the_profile_and_its_exclusions_account_for_every_public_mutation():
	"""The drift alarm.

	Every public mutating verb is either authorized by the profile or
	recorded as deliberately excluded. A new one belongs in one of those
	two places, chosen by a person — this case exists so that choice
	cannot be skipped by accident, NOT so the profile follows the
	registry automatically.
	"""
	sys.path.insert(0, os.path.join(REPO, "src"))
	from baton_work.cli import MUTATIONS

	accounted = set(PROFILE) | {verb for group in EXCLUDED.values()
	                            for verb in group}
	unaccounted = sorted(MUTATIONS - accounted)
	assert not unaccounted, (
		f"public mutation(s) {unaccounted} are neither in the managed-workflow "
		f"profile nor in its recorded exclusions. Decide which, and record it "
		f"in work/records/2026/08/finding-managed-turn-workflow-policy/ "
		f"before adding it here — a mutation must never join the policy "
		f"merely because the CLI registry grew.")
	stale = sorted(accounted - set(MUTATIONS))
	assert not stale, (
		f"{stale} are named by the policy profile or its exclusions but are "
		f"no longer public mutations; the policy would authorize or forbid a "
		f"verb that does not exist")


def test_every_ruled_verb_is_a_real_mutating_verb():
	"""A rule for a verb the CLI does not have authorizes nothing and
	hides a typo behind a green preflight."""
	sys.path.insert(0, os.path.join(REPO, "src"))
	from baton_work.cli import MUTATIONS

	for verb in PROFILE:
		assert verb in MUTATIONS, f"{verb} is not a public mutating verb"


def test_the_generator_emits_one_exact_rule_per_ruled_verb():
	proc = subprocess.run(
		["node", EXEC_POLICY, "binary=/opt/baton/bin/baton",
		 "config=/srv/baton/baton.json", "participant=baton.codex"],
		capture_output=True, text=True, timeout=60)
	assert proc.returncode == 0, proc.stderr
	rules = proc.stdout.splitlines()
	assert len(rules) == len(PROFILE)
	pattern = re.compile(
		r'^prefix_rule\(pattern=\["/opt/baton/bin/baton", "--config", '
		r'"/srv/baton/baton\.json", "--participant", "baton\.codex", '
		r'"([a-z-]+)"\], decision="allow"\)$')
	emitted = []
	for rule in rules:
		match = pattern.match(rule)
		assert match, f"unexpected rule shape: {rule}"
		emitted.append(match.group(1))
	# Order is part of the ruling: an operator diffing a regenerated file
	# against the recorded profile should see no reordering noise.
	assert tuple(emitted) == PROFILE
	for group in EXCLUDED.values():
		for verb in group:
			assert verb not in emitted


def test_the_workflow_a_managed_reviewer_actually_needs_is_authorized():
	"""The concrete failure W220 records: a managed reviewer claimed
	W126, finished its review, and could not `mark-seen` its own
	discussion. The turn escalated, the non-interactive dispatcher
	refused, and the Work stayed claimed by a runner whose turn was over.
	"""
	# Take it, read it, discuss it, hand it back — and recover it.
	for verb in ("claim", "mark-seen", "say", "bind", "pass", "close",
	             "release", "heartbeat"):
		assert verb in PROFILE, f"the managed workflow cannot complete without {verb}"
	# Answer a directed obligation, all three dispositions.
	for verb in ("respond", "accept", "dispose"):
		assert verb in PROFILE
	# But never the deployment, runtime-publication or incident verbs.
	for verb in ("activate", "regen", "runtime-state", "incident", "dismiss"):
		assert verb not in PROFILE
