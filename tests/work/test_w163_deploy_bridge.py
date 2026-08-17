"""W163 (distribution rounds R12-R14): the generic ACP readiness client
co-deploys through the ACTUAL v11 deployer as a READY product.

Everything runs against temporary targets. The deployed release must be
usable exactly as published: stable entry points for both products,
runtime dependencies already resolved inside the immutable target, inert
non-secret example configurations, correct modes, and a refusal BEFORE
atomic publication when dependency assembly cannot complete.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
DEPLOYER = os.path.join(REPO, "tools", "deploy_work.py")

pytestmark = pytest.mark.skipif(
	shutil.which("node") is None or shutil.which("npm") is None,
	reason="the co-deployed bridge needs node/npm at build time")


def _deploy(target, env=None):
	return subprocess.run([sys.executable, DEPLOYER, target],
	                      capture_output=True, text=True, timeout=300,
	                      env=env)


@pytest.fixture(scope="module")
def release(tmp_path_factory):
	target = os.path.join(str(tmp_path_factory.mktemp("w163")), "release")
	proc = _deploy(target)
	assert proc.returncode == 0, proc.stderr
	return target, json.loads(proc.stdout)


def test_both_products_expose_stable_executable_entry_points(release):
	target, facts = release
	for name in ("baton", "acp-baton-bridge"):
		path = os.path.join(target, "bin", name)
		assert os.path.isfile(path), f"bin/{name} missing"
		mode = stat.S_IMODE(os.stat(path).st_mode)
		assert mode == 0o755, f"bin/{name} mode {oct(mode)}"
	assert facts["acp_bridge"] == os.path.join(
		target, "bin", "acp-baton-bridge")


def test_the_examples_are_present_inert_and_non_secret(release):
	target, _facts = release
	for name in ("acp-bridge-claude.example.json",
	             "acp-bridge-gemini.example.json"):
		path = os.path.join(target, "conf", name)
		assert os.path.isfile(path), f"conf/{name} missing"
		with open(path, encoding="utf-8") as handle:
			document = json.load(handle)
		text = json.dumps(document)
		assert "<" in text and ">" in text, \
			"the example lost its explicit placeholders"
		assert document["baton"]["binary"].startswith("<"), \
			"a runnable default replaced the placeholder"
		assert "/home/" not in text, \
			"a host-specific inferred path leaked into the example"


def test_the_pinned_runtime_is_already_inside_the_target(release):
	target, _facts = release
	runtime = os.path.join(target, "lib", "acp-baton-bridge")
	sdk = os.path.join(runtime, "node_modules",
	                   "@agentclientprotocol", "sdk", "package.json")
	assert os.path.isfile(sdk), \
		"the pinned SDK is not resolved inside the immutable target"
	with open(sdk, encoding="utf-8") as handle:
		installed = json.load(handle)["version"]
	with open(os.path.join(runtime, "package.json"),
	          encoding="utf-8") as handle:
		pinned = json.load(handle)["dependencies"]["@agentclientprotocol/sdk"]
	assert installed == pinned, \
		f"target carries {installed}, the lockfile pins {pinned}"
	# The shared projection-5 gate the bridge imports travels beside it.
	assert os.path.isfile(os.path.join(
		target, "lib", "codex-event-bridge", "src",
		"codex_baton_bridge.mjs"))


def test_the_bridge_runs_from_the_target_without_checkout_npm_or_network(
		release, tmp_path):
	target, _facts = release
	# The release requires only node (documented); the PATH here keeps
	# node through a shim directory while npm disappears entirely, and
	# PYTHONPATH is absent — the target must stand alone.
	shim = tmp_path / "shim-bin"
	shim.mkdir()
	os.symlink(shutil.which("node"), shim / "node")
	env = {key: value for key, value in os.environ.items()
	       if key not in ("PYTHONPATH", "npm_config_cache")}
	env["PATH"] = os.pathsep.join(
		[str(shim)] + [entry for entry in env["PATH"].split(os.pathsep)
		               if not os.path.isfile(os.path.join(entry, "npm"))
		               and not os.path.isfile(os.path.join(entry, "node"))])
	assert shutil.which("npm", path=env["PATH"]) is None, \
		"the rig failed to remove npm from PATH"
	assert shutil.which("node", path=env["PATH"]) is not None
	helped = subprocess.run(
		[os.path.join(target, "bin", "acp-baton-bridge"), "--help"],
		capture_output=True, text=True, timeout=60, env=env)
	assert helped.returncode == 0, helped.stderr
	assert "usage: acp-baton-bridge" in helped.stdout
	# The complete shipped acceptance suite, offline, from the target.
	suite = subprocess.run(
		["node", "--test", "test/acp_baton_bridge.test.mjs"],
		cwd=os.path.join(target, "lib", "acp-baton-bridge"),
		capture_output=True, text=True, timeout=300, env=env)
	assert suite.returncode == 0, suite.stdout[-1200:]
	assert "fail 0" in suite.stdout.replace("ℹ", "")


def test_incomplete_dependency_assembly_refuses_before_publication(tmp_path):
	target = os.path.join(str(tmp_path), "refused-release")
	env = dict(os.environ)
	# npm unavailable: assembly cannot complete, so the deployment must
	# refuse and the target must never become visible.
	env["PATH"] = os.pathsep.join(
		entry for entry in env["PATH"].split(os.pathsep)
		if not os.path.isfile(os.path.join(entry, "npm")))
	proc = _deploy(target, env=env)
	assert proc.returncode != 0
	assert "refusing" in proc.stderr
	assert not os.path.lexists(target), \
		"a failed assembly still published a target"
