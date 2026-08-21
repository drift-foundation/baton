"""The v11-only deployer: an explicit immutable distribution root.

Everything here runs against TEMPORARY targets only (the pinned boundary:
automated acceptance never touches a real distribution, coordination home,
or anything v10). The deployed product is exercised as installed — the
executable zipapp with PYTHONPATH absent, template assets as siblings.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures                                               # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
DEPLOYER = os.path.join(REPO, "tools", "deploy_work.py")


def _read(path):
	with open(path, "rb") as handle:
		return handle.read()


def _deploy(target):
	return subprocess.run([sys.executable, DEPLOYER, target],
	                      capture_output=True, text=True, timeout=120)


def _env():
	return {key: value for key, value in os.environ.items()
	        if key != "PYTHONPATH"}


def _run(executable, *argv):
	return subprocess.run([executable] + list(argv), capture_output=True,
	                      text=True, timeout=120, env=_env())


def test_the_operator_deploy_surface_is_the_just_recipe():
	"""The Python packager is internal machinery, not the launch command
	handed to a human at the parallel-trial gate."""
	justfile = _read(os.path.join(REPO, "justfile")).decode("utf-8")
	quickstart = _read(os.path.join(REPO, "docs",
	                                "BATON-WORK.md")).decode("utf-8")
	assert "deploy-v11 DESTINATION:" in justfile
	assert 'python3 tools/deploy_work.py "{{DESTINATION}}"' in justfile
	assert "just deploy-v11 /your/dist/baton-rN" in quickstart
	assert "python3 tools/deploy_work.py" not in quickstart


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
	target = os.path.join(str(tmp_path_factory.mktemp("v11dist")),
	                      "baton-r1")
	proc = _deploy(target)
	assert proc.returncode == 0, proc.stderr
	return target, json.loads(proc.stdout)


def test_the_deployed_layout_is_the_ruled_release_shape(dist):
	target, summary = dist
	executable = os.path.join(target, "bin", "baton")
	assert summary["executable"] == executable
	assert os.stat(executable).st_mode & stat.S_IXUSR, \
		"the deployed product is not executable"
	assert hashlib.sha256(_read(executable)).hexdigest() == \
		summary["archive_sha256"]
	# M6: the numbered templates are SIBLING assets, byte-equal to the
	# source, never zipapp-embedded.
	deployed = os.path.join(target, "tmpl", "work-basic-1.md")
	assert _read(deployed) == _read(os.path.join(REPO, "tmpl",
	                                             "work-basic-1.md"))
	assert b"work-basic-1.md" not in _read(executable), \
		"a template asset leaked into the zipapp"
	# R102 + W163: the COMPLETE distribution — executable,
	# documentation, configuration examples, template assets, and the
	# co-deployed ACP bridge runtime under lib/.
	assert sorted(os.listdir(target)) == ["bin", "conf", "doc", "lib",
	                                      "tmpl"]
	# W2 (negative artifact pin), amended by the W163 distribution
	# ruling: bin/ ships EXACTLY the two product entry points — the
	# retired baton-work name, or any third file smuggled into bin/,
	# fails the gate rather than shipping extra spellings.
	assert sorted(os.listdir(os.path.join(target, "bin"))) == \
		["acp-baton-bridge", "baton"], \
		"bin/ must contain exactly the two product entry points"
	assert _read(os.path.join(target, "doc", "BATON-WORK.md")) == \
		_read(os.path.join(REPO, "docs", "BATON-WORK.md"))
	# W103: the AGENT POLICY ships with the release too, so a
	# participating team bootstraps its agent contract from the same
	# exact release as its CLI rather than from whatever the source
	# checkout happens to say today.
	deployed_policy = _read(os.path.join(target, "doc",
	                                     "AGENTS-MAILBOX-PROTO.md"))
	assert deployed_policy == \
		_read(os.path.join(REPO, "docs", "AGENTS-MAILBOX-PROTO.md")), \
		"the deployed agent policy drifted from source"
	assert b"protocol 11" in deployed_policy, \
		"the deployed agent policy does not name protocol 11"
	# W104: the OPERATING GUIDE ships for the same reason, and the
	# finding requires its examples to be executed against the release
	# that carries them — a drifted copy would document a grammar the
	# shipped executable does not have.
	deployed_guide = _read(os.path.join(target, "doc",
	                                    "EFFECTIVE-BATON.md"))
	assert deployed_guide == \
		_read(os.path.join(REPO, "docs", "EFFECTIVE-BATON.md")), \
		"the deployed operating guide drifted from source"
	assert b"protocol-11" in deployed_guide, \
		"the deployed operating guide does not name protocol 11"
	assert b"send-notice" not in deployed_guide, \
		"the deployed operating guide still prescribes retired v10 tooling"
	example = os.path.join(target, "conf", "baton.example.json")
	assert _read(example) == _read(os.path.join(REPO, "conf",
	                                            "baton.example.json"))
	infra_example = os.path.join(target, "conf", "infra.example.json")
	assert _read(infra_example) == _read(os.path.join(REPO, "conf",
	                                                  "infra.example.json"))
	# The shipped example is a VALID strict document, provable by the
	# product's own loader.
	sys.path.insert(0, os.path.join(REPO, "src"))
	from baton_work import config as work_config
	assert work_config.load(example)["teams"]


def test_an_exact_release_directory_is_immutable(dist, tmp_path):
	target, _summary = dist
	before = _read(os.path.join(target, "bin", "baton"))
	proc = _deploy(target)
	assert proc.returncode == 1
	error = json.loads(proc.stderr)["error"]
	assert "already exists" in error and "NEW explicit" in error
	assert _read(os.path.join(target, "bin", "baton")) == before
	# A missing parent refuses rather than being invented.
	proc = _deploy(str(tmp_path / "absent" / "release"))
	assert proc.returncode == 1
	assert "not an existing directory" in json.loads(proc.stderr)["error"]


def test_the_installed_product_runs_the_whole_onboarding_story(dist,
		tmp_path):
	"""init → edit → activate → create → home → bootstrap, every act the
	INSTALLED executable with no PYTHONPATH — and bootstrap vendors the
	DEPLOYED sibling tmpl/, proving the release-layout asset resolution."""
	target, _summary = dist
	executable = os.path.join(target, "bin", "baton")
	home = str(tmp_path / "home")
	os.mkdir(home)
	proc = _run(executable, "init", f"directory={home}")
	assert proc.returncode == 0, proc.stderr
	config_path = os.path.join(home, "baton.json")
	document = json.loads(_read(config_path))
	document["teams"] = fixtures.config_document(
		{"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})["teams"]
	project = str(tmp_path / "project")
	os.mkdir(project)
	document["roots"] = {"pushcoin": {"display": "PushCoin",
	                                  "base": project}}
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	proc = _run(executable, "--participant", "push.sl", "activate", f"directory={home}")
	assert proc.returncode == 0, proc.stderr
	proc = _run(executable, "--config", config_path,
	            "--participant", "push.sl", "create", "team=push", "kind=bug",
	            "title=first trial work",
	            "origin=self-initiated", "classification=suspected-defect", "body=hello v11")
	assert proc.returncode == 0, proc.stderr
	proc = _run(executable, "--config", config_path,
	            "--participant", "push.sl", "home")
	assert proc.returncode == 0, proc.stderr
	rows = json.loads(proc.stdout)["result"]["rows"]
	assert [row["title"] for row in rows] == ["first trial work"]

	# W4: bootstrap resolves its root through the accepted baton.json.
	proc = _run(executable, "--config", config_path,
	            "bootstrap", "root=pushcoin")
	assert proc.returncode == 0, proc.stderr
	assert _read(os.path.join(project, "tmpl", "work-basic-1.md")) == \
		_read(os.path.join(target, "tmpl", "work-basic-1.md")), \
		"bootstrap did not vendor the deployed sibling assets"

	# The handoff command itself: the DEPLOYED executable's TUI on a
	# real PTY renders the created work and exits clean.
	import pty as _pty
	if hasattr(_pty, "fork"):
		import ptyharness
		text, status, steps = ptyharness.drive(
			config_path, "push.sl", [(b"", 0.5), (b"qy", 0.4)],
			command=[executable])
		screen = ptyharness.replay(steps[0])
		assert any("first trial work" in line for line in screen), \
			screen[:6]
		assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def _snapshot(root):
	entries = {}
	for base, _dirs, files in os.walk(root):
		for name in files:
			path = os.path.join(base, name)
			info = os.stat(path)
			entries[os.path.relpath(path, root)] = (
				info.st_ino, info.st_mtime_ns,
				hashlib.sha256(_read(path)).hexdigest())
	return entries


def test_deploy_and_onboarding_touch_nothing_outside_their_targets(
		dist, tmp_path):
	"""R103: containment is proven against an isolated CANARY tree —
	never by probing anything live. The whole deploy + onboarding story
	runs beside a populated foreign directory whose every byte, inode,
	and mtime must survive unchanged."""
	canary = str(tmp_path / "canary")
	os.makedirs(os.path.join(canary, "nested"))
	for relative in ("a.json", "nested/b.sqlite3", "nested/c.md"):
		with open(os.path.join(canary, relative), "wb") as handle:
			handle.write(relative.encode() + b" canary bytes")
	before = _snapshot(canary)

	target = str(tmp_path / "second-release")
	proc = _deploy(target)
	assert proc.returncode == 0, proc.stderr
	executable = os.path.join(target, "bin", "baton")
	home = str(tmp_path / "home2")
	os.mkdir(home)
	assert _run(executable, "init", f"directory={home}").returncode == 0
	config_path = os.path.join(home, "baton.json")
	document = json.loads(_read(config_path))
	document["teams"] = fixtures.config_document(
		{"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	assert _run(executable, "--participant", "push.sl", "activate",
	            f"directory={home}").returncode == 0
	assert _run(executable, "--config", config_path,
	            "--participant", "push.sl", "create", "team=push", "kind=bug",
	            "title=contained", "origin=self-initiated", "classification=suspected-defect",
	            "body=canary run").returncode == 0

	assert _snapshot(canary) == before, \
		"the deploy/onboarding story reached outside its targets"


def test_the_deployed_archive_contains_no_checkout_bytecode(dist):
	"""A release is assembled from intentional source, not whatever
	interpreter residue happens to be present in the checkout."""
	target, _summary = dist
	executable = os.path.join(target, "bin", "baton")
	with zipfile.ZipFile(executable) as archive:
		members = archive.namelist()
	residue = [name for name in members
	           if "__pycache__" in name or name.endswith(".pyc")]
	assert residue == [], f"checkout bytecode leaked into the release: {residue}"


def test_installed_init_requires_its_release_configuration_assets(tmp_path):
	"""The pinned onboarding model scaffolds from the exact release's
	configuration examples; it may not silently substitute embedded constants
	when that sibling payload is missing."""
	target = str(tmp_path / "release")
	proc = _deploy(target)
	assert proc.returncode == 0, proc.stderr
	os.unlink(os.path.join(target, "conf", "baton.example.json"))
	home = str(tmp_path / "home-without-conf")
	os.mkdir(home)
	proc = _run(os.path.join(target, "bin", "baton"), "init", f"directory={home}")
	assert proc.returncode == 1
	assert "conf" in proc.stderr and "baton.example.json" in proc.stderr


def test_the_deployed_archive_carries_sources_only(dist):
	"""R111: the archive member list is intentional content — no
	host-generated bytecode, no interpreter residue."""
	import zipfile
	target, _summary = dist
	executable = os.path.join(target, "bin", "baton")
	# The zipapp may carry a shebang prefix; zipfile handles it.
	with zipfile.ZipFile(executable) as archive:
		members = archive.namelist()
	assert members, "the archive is empty"
	for member in members:
		assert "__pycache__" not in member and \
			not member.endswith((".pyc", ".pyo")), \
			f"interpreter residue was published: {member}"
	assert any(member.endswith("baton_work/cli.py")
	           for member in members)


def test_installed_init_scaffolds_from_the_release_assets(dist, tmp_path):
	"""R107: the scaffold CONTENT is the release's own assets — the
	setup document byte-for-byte, and the configuration
	example's skeleton with the demonstration teams/roots reset and a
	fresh authority uuid substituted."""
	target, _summary = dist
	executable = os.path.join(target, "bin", "baton")
	home = str(tmp_path / "home")
	os.mkdir(home)
	assert _run(executable, "init", f"directory={home}").returncode == 0
	assert _read(os.path.join(home, "BATON-SETUP.md")) == \
		_read(os.path.join(target, "doc", "BATON-SETUP.md")), \
		"the setup document is not the release asset byte-for-byte"
	example = json.loads(_read(os.path.join(target, "conf",
	                                        "baton.example.json")))
	document = json.loads(_read(os.path.join(home, "baton.json")))
	assert document["teams"] == {} and document["roots"] == {}
	assert document["config_version"] == example["config_version"]
	assert document["protocol_version"] == example["protocol_version"]
	assert document["instance"]["database"] == \
		example["instance"]["database"]
	assert document["instance"]["authority_uuid"] != \
		example["instance"]["authority_uuid"]


# -- The INSTALLED execution-policy generator ------------------------------
#
# `work/records/2026/08/finding-deployed-exec-policy-helper/`. Release
# d46ab1e shipped a dispatcher template instructing the operator to
# generate the exact W415 rules with
# `tools/codex-event-bridge/src/exec_policy.mjs` — a path that exists
# only in the source checkout — and shipped no equivalent installed
# command. A standalone deployment could not follow its own
# instructions, which leaves somebody hand-authoring the
# security-sensitive rules the module exists to get right.
#
# These cases run against the ACTUAL deployer's output rather than a
# synthetic copy list, because the defect was in what the deployer
# copied.

SOURCE_EXEC_POLICY = os.path.join(
	REPO, "tools", "codex-event-bridge", "src", "exec_policy.mjs")
# The confirmed managed-workflow profile
# (`work/records/2026/08/finding-managed-turn-workflow-policy/`,
# 2026-08-21), and the public mutations it deliberately excludes. Both
# are written out here: a deployed artifact that authorized something the
# ruling did not name must fail these cases, and a check that read the
# artifact's own list could never notice.
MANAGED_WORKFLOW = (
	"create", "accept", "respond", "dispose", "close", "block", "unblock",
	"mark-seen", "classify", "claim", "release", "prioritize", "pass",
	"heartbeat", "phase", "try", "extend", "report", "assess", "abandon",
	"revise", "start-thread", "say", "label", "unlabel", "bind", "poke",
	"poke-answer", "poke-cancel", "reroute",
)
EXCLUDED_MUTATIONS = (
	"activate", "regen", "runtime-start", "runtime-state", "runtime-end",
	"runtime-facts", "runtime-refresh", "incident", "dismiss",
)
DEPLOYED_EXEC_POLICY = os.path.join(
	"lib", "codex-event-bridge", "src", "exec_policy.mjs")
POLICY_IDENTITY = ("binary=/opt/baton/bin/baton",
                   "config=/srv/baton/baton.json",
                   "participant=baton.codex")

# The deployed artifact must keep every W415 property, so the matrix is
# driven through the DEPLOYED module's own exports. It asserts and exits
# nonzero rather than reporting, so a regression fails the Python case.
DEPLOYED_POLICY_MATRIX = r"""
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const { rulesFor, auditRules, assertPolicyProvisioned, RULED_VERBS } =
	await import(pathToFileURL(process.argv[2]).href);

const identity = { binary: "/opt/baton/bin/baton",
	config: "/srv/baton/baton.json", participant: "baton.codex" };
const other = { ...identity, participant: "baton.tuner" };
// The confirmed managed-workflow profile, written out here rather than
// read from the deployed module: a copy that authorized a verb the
// ruling did not name must fail this, and comparing the module with
// itself never could.
assert.deepEqual(RULED_VERBS, [
	"create", "accept", "respond", "dispose", "close", "block", "unblock",
	"mark-seen", "classify", "claim", "release", "prioritize", "pass",
	"heartbeat", "phase", "try", "extend", "report", "assess", "abandon",
	"revise", "start-thread", "say", "label", "unlabel", "bind", "poke",
	"poke-answer", "poke-cancel", "reroute",
], "the deployed ruled capability is not the confirmed managed-workflow profile");
const exact = rulesFor(identity).join("\n");
const dir = mkdtempSync("/tmp/deployed-exec-policy-");
const write = (name, text) => {
	const file = join(dir, name);
	writeFileSync(file, `${text}\n`);
	return file;
};
const broadRule = `prefix_rule(pattern=["${identity.binary}"], decision="allow")`;
const ruleFor = (who, verb) =>
	`prefix_rule(pattern=["${identity.binary}", "--config", `
	+ `"${identity.config}", "--participant", "${who}", "${verb}"], `
	+ `decision="allow")`;

// EXACT ONLY is the approved state and still succeeds.
assert.equal(assertPolicyProvisioned(write("exact.rules", exact),
	identity).satisfied, true);

// EXACT + BROAD: the half-finished upgrade an operator most likely has.
assert.throws(() => assertPolicyProvisioned(
	write("mixed.rules", `${exact}\n${broadRule}`), identity),
	/half-finished upgrade state/);

// BROAD ONLY refuses, with the install instructions.
assert.throws(() => assertPolicyProvisioned(write("broad.rules", broadRule),
	identity), /install these rules and remove the broad one/);

// Any other verb for THIS participant is extra capability — the
// deliberately excluded deployment, runtime and incident mutations
// especially, plus a pure read.
for (const verb of ["activate", "regen", "runtime-start", "runtime-state",
                    "runtime-end", "runtime-facts", "runtime-refresh",
                    "incident", "dismiss", "detail"]) {
	const policy = `${exact}\n${ruleFor(identity.participant, verb)}`;
	assert.deepEqual(auditRules(policy, identity).extra, [verb]);
	assert.throws(() => assertPolicyProvisioned(write(`${verb}.rules`, policy),
		identity), /dedicated to the approved 'managed-work-workflow' set/);
}

// W220 round 1: a prefix rule may carry OPERANDS, and an
// excluded verb with one used to audit as satisfied. The deployed
// artifact must refuse it too.
for (const verb of ["regen", "activate", "runtime-state", "dismiss",
                    "teleport"]) {
	const qualified = `prefix_rule(pattern=["${identity.binary}", "--config", `
		+ `"${identity.config}", "--participant", "${identity.participant}", `
		+ `"${verb}", "op-id=authorized-extra"], decision="allow")`;
	const policy = `${exact}\n${qualified}`;
	assert.deepEqual(auditRules(policy, identity).extra, [verb]);
	assert.throws(() => assertPolicyProvisioned(
		write(`qualified-${verb}.rules`, policy), identity),
		/dedicated to the approved 'managed-work-workflow' set/);
}
// A RULED verb with operands is a subset of a granted capability.
assert.equal(assertPolicyProvisioned(write("ruled-qualified.rules",
	`${exact}\nprefix_rule(pattern=["${identity.binary}", "--config", `
	+ `"${identity.config}", "--participant", "${identity.participant}", `
	+ `"claim", "work=W1"], decision="allow")`), identity).satisfied, true);

// Other participants' rules are independent and stay valid.
assert.equal(assertPolicyProvisioned(
	write("other-extra.rules", `${exact}\n${ruleFor(other.participant, "regen")}`),
	identity).satisfied, true);

process.stdout.write("matrix ok\n");
"""


# The shipped template configures MORE THAN ONE target identity and
# `EventBridge.start()` preflights every one of them against the single
# nominated `execPolicyFile`, so provisioning is only complete when that
# one file carries the exact rules for ALL of them. This drives the
# DEPLOYED auditor over both the combined file and a one-participant
# file, because the one-participant file is what the previous
# instruction produced.
TEMPLATE_PROVISIONING_CHECK = r"""
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

const [modulePath, combined, partial, binary, config, ...participants] =
	process.argv.slice(2);
const { assertPolicyProvisioned } =
	await import(pathToFileURL(modulePath).href);

assert.ok(participants.length > 1,
	"the shipped template configures only one identity; this case is about "
	+ "the several-identity provisioning path");

// The documented combined file authorizes every configured identity.
for (const participant of participants) {
	assert.equal(
		assertPolicyProvisioned(combined, { binary, config, participant }).satisfied,
		true, `the combined policy does not authorize ${participant}`);
}

// And following the instruction for ONE participant leaves the others
// unauthorized — which is why the instruction must say "once per
// participant, appended". The dispatcher refuses to start in this state.
assert.equal(
	assertPolicyProvisioned(partial, { binary, config, participant: participants[0] })
		.satisfied, true);
for (const participant of participants.slice(1)) {
	assert.throws(
		() => assertPolicyProvisioned(partial, { binary, config, participant }),
		/does not authorize/,
		`a one-participant policy still authorized ${participant}`);
}

process.stdout.write("provisioning ok\n");
"""


def _node(*argv, **kwargs):
	return subprocess.run(["node", *argv], capture_output=True, text=True,
	                      timeout=120, env=_env(), **kwargs)


def test_the_release_carries_the_generator_its_template_names(dist):
	"""The release carries a BYTE-EQUAL IMMUTABLE COPY of the reviewed
	source helper. It is not the same filesystem artifact the dispatcher
	imports — the canonical dispatcher runs from a source checkout and
	this release ships no bin/codex-event-bridge — so byte parity is the
	whole guarantee that the operator's generator and the dispatcher's
	auditor are one implementation."""
	target, _summary = dist
	deployed = os.path.join(target, DEPLOYED_EXEC_POLICY)
	assert os.path.isfile(deployed), \
		"the release ships no execution-policy generator"
	assert _read(deployed) == _read(SOURCE_EXEC_POLICY), \
		"the deployed generator drifted from the reviewed source module"
	# The W163 distribution ruling's two product entry points are
	# UNCHANGED: the generator ships in the private lib/ location the
	# shared bridge modules already use, not as a third bin/ command.
	assert sorted(os.listdir(os.path.join(target, "bin"))) == \
		["acp-baton-bridge", "baton"], \
		"the generator was smuggled in as a third product entry point"


def test_the_shipped_template_names_only_installed_resources(dist):
	"""A standalone deployment must be able to follow its own
	instructions; the checkout locator it used to print is not a
	resource the operator has."""
	target, _summary = dist
	shipped = os.path.join(target, "conf",
	                       "codex-event-bridge.template.json")
	document = json.loads(_read(shipped))
	comment = "\n".join(value for key, value in document.items()
	                    if key.startswith("//"))
	assert "lib/codex-event-bridge/src/exec_policy.mjs" in comment, \
		"the template does not name the installed generator"
	assert "tools/codex-event-bridge" not in comment, \
		"the template still instructs the operator to use a checkout path"
	# The instruction is a runnable invocation, in the operand grammar
	# the generator actually accepts.
	for operand in ("binary=", "config=", "participant="):
		assert operand in comment, f"the instruction omits {operand}"
	# It provisions EVERY configured identity, because the dispatcher
	# preflights each of them against this one nominated file. A single
	# run leaves the rest unauthorized, and a second `>` would drop the
	# first, so the documented form appends into a staged file.
	for entry in document["targets"].values():
		participant = entry["identity"]["participant"]
		assert participant in comment, \
			f"the instruction never provisions {participant}"
	assert ">>" in comment, \
		"the instruction does not append each participant's rules"
	assert "staged" in comment, \
		"the instruction redirects onto the live policy file"
	# It ships byte-equal to source, so the two cannot drift.
	assert _read(shipped) == _read(os.path.join(
		REPO, "conf", "codex-event-bridge.template.json"))


def test_the_deployed_generator_emits_the_approved_rules_standalone(dist):
	"""Run from the immutable target with no checkout on the path — the
	release is what an operator has, and it must produce byte-identical
	output to the reviewed helper."""
	target, _summary = dist
	deployed = _node(os.path.join(target, DEPLOYED_EXEC_POLICY),
	                 *POLICY_IDENTITY, cwd=target)
	assert deployed.returncode == 0, deployed.stderr
	source = _node(SOURCE_EXEC_POLICY, *POLICY_IDENTITY)
	assert source.returncode == 0, source.stderr
	assert deployed.stdout == source.stdout, \
		"the deployed generator's output drifted from the reviewed helper"
	assert deployed.stderr == "", "the generator wrote to stderr on success"
	# Independently of that parity: the approved profile, in the ruled
	# order, each rule naming the exact executable, config and
	# participant. The expected verbs are listed here rather than read
	# from the artifact under test.
	lines = deployed.stdout.split("\n")
	assert lines[-1] == "", "the generator did not end with a final newline"
	assert lines[:-1] and len(lines) == len(MANAGED_WORKFLOW) + 1, \
		f"the generator printed {len(lines) - 1} rules, not " \
		f"{len(MANAGED_WORKFLOW)}"
	for verb, rule in zip(MANAGED_WORKFLOW, lines):
		assert rule == (
			'prefix_rule(pattern=["/opt/baton/bin/baton", "--config", '
			'"/srv/baton/baton.json", "--participant", "baton.codex", '
			f'"{verb}"], decision="allow")')
	# W220: the operation whose absence stranded a claimed Work, and the
	# rest of the workflow that has to follow it.
	for verb in ("mark-seen", "respond", "release", "heartbeat", "pass"):
		assert verb in MANAGED_WORKFLOW
		assert f'"{verb}"], decision="allow")' in deployed.stdout
	# And nothing the profile excludes.
	for verb in EXCLUDED_MUTATIONS:
		assert f'"{verb}"], decision="allow")' not in deployed.stdout, \
			f"the deployed generator emitted a rule for excluded {verb}"
	# It PRINTS and never installs: a generator that could write the
	# policy file could grant itself authority.
	assert not os.path.exists(os.path.join(target, "baton.rules"))


def test_the_deployed_generator_refuses_every_malformed_invocation(dist):
	"""Strict operands, from the installed artifact. A generator that
	guessed would emit rules authorizing a command nobody asked for."""
	target, _summary = dist
	deployed = os.path.join(target, DEPLOYED_EXEC_POLICY)
	refusals = (
		((), "missing operand(s): binary, config, participant"),
		(POLICY_IDENTITY[:2], "missing operand(s): participant"),
		(POLICY_IDENTITY + ("verbs=claim",), 'unknown operand "verbs=claim"'),
		(POLICY_IDENTITY + (POLICY_IDENTITY[0],),
		 "operand binary was given more than once"),
		(("binary",) + POLICY_IDENTITY[1:], "operand binary needs a value"),
		(("binary=bin/baton",) + POLICY_IDENTITY[1:],
		 "ABSOLUTE installed executable"),
		((POLICY_IDENTITY[0], "config=baton.json", POLICY_IDENTITY[2]),
		 "ABSOLUTE installed executable"),
		((POLICY_IDENTITY[0], POLICY_IDENTITY[1], "participant="),
		 "non-empty participant"),
	)
	for argv, expected in refusals:
		proc = _node(deployed, *argv, cwd=target)
		assert proc.returncode != 0, f"{argv} was not refused"
		assert expected in proc.stderr, f"{argv}: {proc.stderr}"
		assert proc.stdout == "", \
			f"{argv} still wrote policy text to stdout"


def test_importing_the_deployed_generator_emits_nothing(dist):
	"""This module is IMPORTED as well as run — the bridge's startup
	preflight imports the source original — so the direct invocation
	must stay inert on import in the shipped copy too."""
	target, _summary = dist
	# The path is EMBEDDED in the script rather than passed as an
	# operand: `node -e` puts extra arguments at argv[1], which is
	# exactly where a directly-invoked module sees its own path.
	deployed = os.path.join(target, DEPLOYED_EXEC_POLICY)
	proc = _node("--input-type=module", "-e",
	             f"await import({json.dumps(deployed)});", cwd=target)
	assert proc.returncode == 0, proc.stderr
	assert proc.stdout == "" and proc.stderr == "", \
		"importing the generator produced output"


def test_the_deployed_artifact_keeps_the_exact_policy_boundary(dist,
		tmp_path):
	"""W415's exact/broad/extra matrix, driven through the DEPLOYED
	module. Shipping the generator must not ship a weaker auditor."""
	target, _summary = dist
	script = tmp_path / "deployed_policy_matrix.mjs"
	script.write_text(DEPLOYED_POLICY_MATRIX, encoding="utf-8")
	proc = _node(str(script), os.path.join(target, DEPLOYED_EXEC_POLICY),
	             cwd=target)
	assert proc.returncode == 0, proc.stderr[-2000:]
	assert proc.stdout.strip() == "matrix ok"


def test_the_shipped_instruction_provisions_every_template_identity(dist,
		tmp_path):
	"""P1: the template nominates ONE execPolicyFile and configures more
	than one target identity, and `EventBridge.start()` preflights every
	one of them against that file. Running the generator once — the
	instruction this release used to ship — leaves the rest
	unauthorized and the dispatcher refusing to start."""
	target, _summary = dist
	template = json.loads(_read(os.path.join(
		target, "conf", "codex-event-bridge.template.json")))
	participants = sorted({entry["identity"]["participant"]
	                       for entry in template["targets"].values()})
	assert len(participants) > 1, \
		"the template no longer exercises the several-identity path"
	binary = template["roleInstructions"]["binary"]
	config = template["roleInstructions"]["config"]
	deployed = os.path.join(target, DEPLOYED_EXEC_POLICY)

	# Exactly the documented procedure: once per participant, APPENDED
	# into a staged file, and only then installed.
	staged = tmp_path / "baton.rules.staged"
	with open(staged, "w", encoding="utf-8") as handle:
		for participant in participants:
			proc = _node(deployed, f"binary={binary}", f"config={config}",
			             f"participant={participant}", cwd=target)
			assert proc.returncode == 0, proc.stderr
			handle.write(proc.stdout)
	installed = tmp_path / "baton.rules"
	os.rename(staged, installed)
	assert len(_read(installed).splitlines()) == \
		len(MANAGED_WORKFLOW) * len(participants)

	# And the single-run form the release used to document.
	partial = tmp_path / "one-participant.rules"
	proc = _node(deployed, f"binary={binary}", f"config={config}",
	             f"participant={participants[0]}", cwd=target)
	assert proc.returncode == 0, proc.stderr
	partial.write_text(proc.stdout, encoding="utf-8")

	script = tmp_path / "template_provisioning.mjs"
	script.write_text(TEMPLATE_PROVISIONING_CHECK, encoding="utf-8")
	proc = _node(str(script), deployed, str(installed), str(partial),
	             binary, config, *participants, cwd=target)
	assert proc.returncode == 0, proc.stderr[-2000:]
	assert proc.stdout.strip() == "provisioning ok"


def test_the_recreation_script_instructs_the_renamed_executable():
	"""W2 R1: the W92 recreation script is CURRENT operator instruction,
	not frozen history — it must name bin/baton and never the retired
	spelling."""
	script = os.path.join(
		os.path.dirname(os.path.dirname(os.path.dirname(
			os.path.abspath(__file__)))),
		"work", "records", "2026", "08",
		"finding-recursive-target-graph", "findings",
		"finding-fresh-record-layout-cutover", "scripts",
		"recreate-work.sh")
	text = open(script, encoding="utf-8").read()
	assert "bin/baton-work" not in text, \
		"the retired executable name survives in current instruction"
	assert "bin/baton" in text


def test_the_recreation_script_parks_as_the_feature_review_handler():
	"""W92 cutover defect: creation may be self-initiated, but changing a
	feature's phase belongs to its configured rview handler."""
	script = os.path.join(
		os.path.dirname(os.path.dirname(os.path.dirname(
			os.path.abspath(__file__)))),
		"work", "records", "2026", "08",
		"finding-recursive-target-graph", "findings",
		"finding-fresh-record-layout-cutover", "scripts",
		"recreate-work.sh")
	text = open(script, encoding="utf-8").read()
	assert 'REVIEWER="--participant baton.codex"' in text
	assert '$REVIEWER phase "op-id=w92-park-wsearch"' in text
