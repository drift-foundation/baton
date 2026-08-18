"""W4: the retired v10 runtime is gone, and stays gone.

The removal itself is a one-time act. What needs protecting is the
boundary it establishes: v10 may survive in historical records and
release notes, because those describe the release they were written for
and are never rewritten to satisfy a scan — but never in a path anything
executes.

These checks are deliberately structural. A file reappearing is easy to
notice in review; a `justfile` recipe or a tool config quietly pointing
at one again is not.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import zipfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))

# The complete ruled removal inventory.
REMOVED_PATHS = (
	"src/baton_core", "src/baton_tui", "compat",
	"tests/core", "tests/tui", "tests/packaging", "tests/candidate.py",
	"tools/build_release.py", "tools/build_zipapp.py",
	"tools/build_tui.py", "tools/deploy.py", "tools/migration_guide.py",
	"tools/publish_guide.py", "tools/retire_release.py",
	"dist", "schema/config-schema.json", "examples/baton.json",
	"tools/codex-event-bridge/src/baton_source.mjs",
	"tools/codex-event-bridge/src/stack.mjs",
	"tools/codex-event-bridge/bin/baton-codex-monitor",
	"tools/codex-event-bridge/bin/codex-baton-stack",
	"tools/codex-event-bridge/test/baton_source.test.mjs",
	"tools/codex-event-bridge/test/stack.test.mjs",
)

# The surface the finding explicitly RETAINS. Asserting this stops the
# removal from being over-applied later by someone reading only the
# first half of the contract.
RETAINED_PATHS = (
	"src/baton_work", "tests/work", "tmpl", "conf/baton.example.json",
	"tools/deploy_work.py", "tools/requirements-dev.txt",
	"tools/acp-baton-bridge",
	"tools/codex-event-bridge/src/codex_baton_bridge.mjs",
	"tools/codex-event-bridge/src/config.mjs",
	"tools/codex-event-bridge/src/send_event.mjs",
	"examples/acp-bridge-claude.json",
)

# Modules and entry points that only ever existed to run protocol 10.
RETIRED_NAMES = ("baton_core", "baton_tui", "baton_source",
                 "codex-baton-stack", "baton-codex-monitor",
                 "tests/candidate.py", "build_zipapp", "build_release",
                 "migration_guide", "publish_guide", "retire_release")

SKIP_DIRS = {"." + "git", "node_modules", "__pycache__", "work", ".venv"}


def _read(relative):
	with open(os.path.join(REPO, relative), encoding="utf-8") as handle:
		return handle.read()


@pytest.mark.parametrize("relative", REMOVED_PATHS)
def test_the_retired_path_is_gone(relative):
	assert not os.path.exists(os.path.join(REPO, relative)), \
		f"{relative} is back"


@pytest.mark.parametrize("relative", RETAINED_PATHS)
def test_the_retained_surface_survived(relative):
	assert os.path.exists(os.path.join(REPO, relative)), \
		f"{relative} was removed, but the finding retains it"


def test_no_operator_recipe_invokes_a_retired_path():
	"""The `justfile` is the operator's entry surface: a recipe naming a
	removed tool fails at the shell, after the operator believed it was
	running something."""
	recipes = _read("justfile")
	for name in RETIRED_NAMES:
		assert name not in recipes, \
			f"a just recipe still names the retired {name!r}"
	assert re.search(r"^default: test-v11$", recipes, re.M), recipes[:200]


def test_the_bridge_configuration_dropped_the_stack_only_fields():
	"""The `baton` block and per-target `participant` were consumed only
	by the retired all-session stack. Keeping them would be dead schema
	that still validates, which is how a removed feature looks alive. The
	retained identity contract may use similar implementation names, so pin
	the public behavior rather than source tokens."""
	script = r'''
import { validateConfig } from "./tools/codex-event-bridge/src/config.mjs";

const legacy = validateConfig({
  baton: { binary: "/opt/baton/bin/baton", config: "/srv/v10.json",
           waitTimeoutSeconds: 30 },
  servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
  targets: {
    a: { server: "local", threadId: "thread-a",
         participant: "baton.reviewer" },
  },
});

let duplicateIdentityError = null;
try {
  validateConfig({
    roleInstructions: {
      binary: "/opt/baton/bin/baton", config: "/srv/v11.json",
    },
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      a: { server: "local", threadId: "thread-a",
           identity: { participant: "baton.tuner", role: "tuner" } },
      b: { server: "local", threadId: "thread-b",
           identity: { participant: "baton.tuner", role: "review" } },
    },
  });
} catch (error) {
  duplicateIdentityError = error.message;
}

console.log(JSON.stringify({
  hasLegacyBaton: Object.hasOwn(legacy, "baton"),
  hasLegacyParticipant: Object.hasOwn(legacy.targets.a, "participant"),
  duplicateIdentityError,
  eventSocket: legacy.eventSocket,
}));
'''
	done = subprocess.run(
		["node", "--input-type=module", "--eval", script], cwd=REPO,
		capture_output=True, text=True, timeout=30)
	assert done.returncode == 0, done.stderr
	result = json.loads(done.stdout)
	assert result["hasLegacyBaton"] is False
	assert result["hasLegacyParticipant"] is False
	assert "baton.tuner is assigned to more than one target" in \
		result["duplicateIdentityError"]
	assert result["eventSocket"], "the retained generic transport disappeared"


def test_no_python_module_imports_the_retired_packages():
	"""Structural, not textual: the import statements themselves."""
	offenders = []
	for base, dirs, files in os.walk(REPO):
		dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
		for name in sorted(files):
			if not name.endswith(".py"):
				continue
			path = os.path.join(base, name)
			try:
				with open(path, encoding="utf-8") as handle:
					tree = ast.parse(handle.read())
			except SyntaxError:
				continue
			for node in ast.walk(tree):
				if isinstance(node, ast.Import):
					names = [alias.name for alias in node.names]
				elif isinstance(node, ast.ImportFrom):
					names = [node.module or ""]
				else:
					continue
				for module in names:
					if module.split(".")[0] in ("baton_core", "baton_tui"):
						offenders.append(
							f"{os.path.relpath(path, REPO)}: {module}")
	assert not offenders, offenders


@pytest.mark.serial
def test_a_fresh_distribution_carries_no_v10(tmp_path):
	"""The shipped artifact, not the checkout: a release is what an
	operator actually receives."""
	target = os.path.join(str(tmp_path), "dist")
	done = subprocess.run(
		[sys.executable, os.path.join(REPO, "tools", "deploy_work.py"),
		 target], capture_output=True, text=True, timeout=180)
	assert done.returncode == 0, done.stderr
	archive = json.loads(done.stdout)["executable"]
	with zipfile.ZipFile(archive) as bundle:
		members = [info.filename for info in bundle.infolist()]
	assert members, "the distribution is empty"
	assert any(name.startswith("baton_work/") for name in members)
	for name in members:
		assert "baton_core" not in name and "baton_tui" not in name, name
	packaged = []
	for base, _dirs, files in os.walk(target):
		packaged += [name for name in files if name.endswith(".mjs")]
	assert "codex_baton_bridge.mjs" in packaged
	assert "baton_source.mjs" not in packaged
	assert "stack.mjs" not in packaged


# -- the gap the first version of this file had ----------------------------
#
# Those checks all read TRACKED paths, so they passed with a mode-0755
# protocol-10 zipapp sitting in `build/` — ignored, invisible to the
# diff, and executable. "No executable fallback" is a property of the
# CHECKOUT, not of the index.

# The retired v10 builder staged its candidate here and marked it with
# this file. Both are pinned by name rather than by a wildcard: a future
# v11 staging design is a separate ruling, and this must refuse the
# retired shape without pre-judging that one.
RETIRED_CANDIDATE_DIR = "build"
RETIRED_CANDIDATE_MARKER = os.path.join("build", "." + "baton-candidate.json")
RETIRED_CANDIDATE_BINARIES = (os.path.join("build", "bin", "baton"),
                              os.path.join("build", "bin", "baton-tui"))


def test_no_retired_candidate_is_staged_in_the_checkout():
	"""The v10 builder is gone, so nothing can legitimately recreate its
	candidate. One left behind is an executable protocol-10 fallback a
	human can still run."""
	marker = os.path.join(REPO, RETIRED_CANDIDATE_MARKER)
	assert not os.path.exists(marker), \
		f"{RETIRED_CANDIDATE_MARKER} marks a staged retired candidate"
	for relative in RETIRED_CANDIDATE_BINARIES:
		assert not os.path.exists(os.path.join(REPO, relative)), \
			f"{relative} is an executable retired candidate"


def test_no_executable_in_the_checkout_bundles_the_retired_packages():
	"""The general form, and the one that would have caught this: an
	executable zipapp ANYWHERE in the tree that carries `baton_core` or
	`baton_tui`. Reads the archive rather than trusting its path."""
	offenders = []
	for base, dirs, files in os.walk(REPO):
		dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
		for name in sorted(files):
			path = os.path.join(base, name)
			if not os.access(path, os.X_OK) or os.path.islink(path):
				continue
			if not zipfile.is_zipfile(path):
				continue
			try:
				with zipfile.ZipFile(path) as bundle:
					members = [info.filename for info in bundle.infolist()]
			except (zipfile.BadZipFile, OSError):
				continue
			for member in members:
				if member.split("/")[0] in ("baton_core", "baton_tui"):
					offenders.append(
						f"{os.path.relpath(path, REPO)} bundles {member}")
					break
	assert not offenders, ("executable protocol-10 fallbacks in the "
	                       "checkout:\n  " + "\n  ".join(offenders))


def test_the_ignore_rules_do_not_hide_a_retired_candidate():
	"""The ignore file is why the candidate was invisible. Its rules for
	the removed builder are gone with it — keeping them would quietly
	re-hide the next one."""
	rules = _read("." + "gitignore")
	for pattern in (RETIRED_CANDIDATE_DIR + "/", ".build-staging-",
	                ".build-retiring-"):
		assert pattern not in rules, \
			f"the ignore file still hides the retired {pattern!r}"


def test_the_surviving_recipes_advertise_no_removed_command():
	"""Guidance is actionable text. A comment in the ONE surviving gate
	telling an operator to run `just build` and `just test` is an
	instruction to run two recipes this change deleted."""
	recipes = _read("justfile")
	declared = set(re.findall(r"^([a-z][a-z0-9-]*)(?: [A-Z_ *]+)*:",
	                          recipes, re.M))
	for referenced in set(re.findall(r"`just ([a-z][a-z0-9-]*)", recipes)):
		assert referenced in declared, \
			(f"the justfile tells an operator to run `just {referenced}`, "
			 f"which it does not define")
