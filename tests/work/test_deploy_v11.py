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
