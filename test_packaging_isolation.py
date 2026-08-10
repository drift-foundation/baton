"""The CLI artifact must not grow because a TUI exists.

Pinned as a regression rather than a convention: `baton` is the agent-to-agent
tool and its distribution must stay small and stable. TUI modules, curses, or
rendering code inside it would mean every agent deployment carries a terminal
UI it never runs -- and that the two front ends had started to fuse.
"""

from __future__ import annotations

import ast
import os
import pathlib
import zipfile

import pytest

HERE = pathlib.Path(__file__).parent
ARTIFACT = HERE / "bin" / "baton"

TUI_MARKERS = ("baton_tui", "curses", "safe_text", "InboxState", "render(")


def test_the_built_cli_contains_no_tui_module():
	"""Inspect the actual shipped zipapp, not the source tree."""
	assert ARTIFACT.exists(), "build the artifact first (just build)"
	with zipfile.ZipFile(ARTIFACT) as archive:
		names = archive.namelist()
	assert names, "artifact is empty"
	for name in names:
		assert "baton_tui" not in name, f"TUI module {name} is inside the CLI artifact"
		assert "curses" not in name, f"curses module {name} is inside the CLI artifact"


def test_the_built_cli_never_imports_curses_or_the_tui():
	"""Absence of a file is not absence of a dependency: a single `import
	curses` would make the agent CLI need a terminal library at startup."""
	with zipfile.ZipFile(ARTIFACT) as archive:
		for name in archive.namelist():
			if not name.endswith(".py"):
				continue
			source = archive.read(name).decode("utf-8", "replace")
			tree = ast.parse(source, filename=name)
			for node in ast.walk(tree):
				if isinstance(node, ast.Import):
					for alias in node.names:
						assert not alias.name.startswith(("curses", "baton_tui")), (
							f"{name} imports {alias.name}")
				elif isinstance(node, ast.ImportFrom) and node.module:
					assert not node.module.startswith(("curses", "baton_tui")), (
						f"{name} imports from {node.module}")


def test_the_core_never_imports_the_front_ends():
	"""Direction of dependency: front ends import the core, never the reverse.
	A core that reached back into a UI could not be packaged without it."""
	for path in sorted((HERE / "baton_core").glob("*.py")):
		tree = ast.parse(path.read_text(), filename=str(path))
		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				for alias in node.names:
					assert not alias.name.startswith(("baton_tui", "curses")), (
						f"{path.name} imports {alias.name}")
			elif isinstance(node, ast.ImportFrom) and node.module:
				assert not node.module.startswith(("baton_tui", "curses")), (
					f"{path.name} imports from {node.module}")


def test_the_tui_never_duplicates_protocol_logic():
	"""One implementation of Baton semantics. The console may import the core
	and stdlib; it may not open SQLite, and it may not shell out to the CLI as
	its normal path -- either would be a second implementation growing."""
	for path in sorted((HERE / "baton_tui").glob("*.py")):
		source = path.read_text()
		tree = ast.parse(source, filename=str(path))
		imported = set()
		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				imported.update(alias.name.split(".")[0] for alias in node.names)
			elif isinstance(node, ast.ImportFrom) and node.module:
				imported.add(node.module.split(".")[0])
		assert "sqlite3" not in imported, f"{path.name} opens the authority directly"
		assert "baton_v6" not in imported, f"{path.name} imports the frozen oracle"
		# `subprocess` is banned everywhere EXCEPT the external editor, which
		# is the one module whose whole job is running another program. The
		# rule this guard exists for is unchanged: no module may run the baton
		# CLI, because doing protocol work by shelling out to it is how a
		# second implementation grows. Running a text editor on a temp file is
		# not that, and never touches the authority.
		if path.name != "editor.py":
			assert "subprocess" not in imported, f"{path.name} shells out"
		# And nothing anywhere invokes the CLI, by name or by path.
		for marker in ("bin/baton", "baton-protocol", '"baton"', "'baton'"):
			assert marker not in source, f"{path.name} invokes the CLI ({marker})"


def test_the_tui_depends_only_on_the_stdlib_and_the_core():
	"""No third-party dependency, matching the CLI's contract. The console
	must stay as installable as the tool it fronts.

	The allowlist is also where a NEW capability becomes visible: adding the
	external editor put `subprocess` in the console, and that is exactly the
	kind of change that should require an edit here rather than slipping in
	behind a pattern match."""
	# An explicit allowlist, not a pattern: every entry is a deliberate
	# decision that the console may depend on it. Adding one should be a
	# visible edit, which is the point -- a third-party import would make the
	# console less installable than the tool it fronts.
	allowed = {"baton_core", "baton_tui",     # the core and this package
	           "curses",                       # the only terminal dependency, stdlib
	           "argparse", "unicodedata", "os", "sys", "json", "time",
	           "locale",                       # terminal encoding, for the divider
	           "textwrap", "__future__", "typing",
	           # The external body editor, added deliberately and each for one
	           # reason. `subprocess` is the notable one: it is how the editor
	           # runs WITHOUT a shell, which is the whole security property --
	           # `os.system` would have needed no new import and would have
	           # been the wrong answer.
	           "subprocess",                   # argv execution, never a shell
	           "shlex",                        # parse a configured command safely
	           "tempfile", "stat"}             # a private draft, checked on return
	for path in sorted((HERE / "baton_tui").glob("*.py")):
		tree = ast.parse(path.read_text(), filename=str(path))
		for node in ast.walk(tree):
			names = []
			if isinstance(node, ast.Import):
				names = [alias.name.split(".")[0] for alias in node.names]
			elif isinstance(node, ast.ImportFrom):
				if node.level:
					continue          # relative: intra-package, not a dependency
				names = [node.module.split(".")[0]] if node.module else []
			for name in names:
				assert name in allowed, f"{path.name} imports unexpected {name!r}"


def test_the_cli_artifact_contains_no_console_code():
	"""The PROPERTY the size ceiling was a proxy for, asserted directly.

	A bare ceiling cannot tell UI leakage from the core legitimately growing,
	and protocol 10 grew it: publications, audiences and their doctor passes
	took the artifact past 300KB with nothing UI-shaped in it. Raising the
	number alone would have weakened the guard to keep it quiet; naming the
	members says what was actually meant.

	The ceiling stays as a second, cruder net -- for a dependency that is
	neither `baton_tui` nor obviously UI -- but it is now the backstop rather
	than the test."""
	import zipfile
	members = zipfile.ZipFile(ARTIFACT).namelist()
	assert members, "the artifact is empty"
	intruders = [name for name in members
	             if not (name == "__main__.py" or name.startswith("baton_core/"))]
	assert intruders == [], f"non-core members in the CLI artifact: {intruders}"

	size = ARTIFACT.stat().st_size
	assert size < 600 * 1024, (
		f"CLI artifact is {size} bytes. Nothing UI-shaped is in it, so this is "
		f"the core growing -- but check that before raising the bound again")


# -- the trial artifact, and what building it must NOT touch --------------

TUI_ARTIFACT = HERE / "bin" / "baton-tui"


def test_the_tui_artifact_carries_the_core_and_the_console():
	assert TUI_ARTIFACT.exists(), "build it with build_tui.py"
	with zipfile.ZipFile(TUI_ARTIFACT) as archive:
		names = set(archive.namelist())
	assert "__main__.py" in names
	assert any(n.startswith("baton_core/") for n in names)
	assert any(n.startswith("baton_tui/") for n in names)
	# It must NOT carry the frozen CLI implementation: one protocol
	# implementation, and the console uses the core.
	assert not any("baton_v6" in n for n in names)


def test_building_the_trial_artifact_leaves_the_cli_untouched(tmp_path):
	"""Slawomir's trial must not perturb the agent channel. The CLI, its
	manifest and its builder stay byte-identical, which is why the trial has
	its own builder and its own manifest rather than an option on the
	existing one -- the surest way to keep something unchanged is for the
	code that changes it never to run."""
	import hashlib
	import subprocess
	import sys

	def digest(path):
		return hashlib.sha256(path.read_bytes()).hexdigest()

	cli_before = digest(HERE / "bin" / "baton")
	manifest_before = digest(HERE / "DISTRIBUTION.json")
	oracle_before = digest(HERE / "baton_v6.py")

	result = subprocess.run([sys.executable, str(HERE / "build_tui.py"), str(tmp_path)],
	                        capture_output=True, text=True, cwd=str(HERE))
	assert result.returncode == 0, result.stderr

	assert digest(HERE / "bin" / "baton") == cli_before
	assert digest(HERE / "DISTRIBUTION.json") == manifest_before
	assert digest(HERE / "baton_v6.py") == oracle_before
	# It wrote its own artifact and its own manifest, elsewhere.
	assert (tmp_path / "bin" / "baton-tui").exists()
	assert (tmp_path / "DISTRIBUTION-TUI.json").exists()
	assert not (tmp_path / "DISTRIBUTION.json").exists()


def test_the_trial_build_is_deterministic(tmp_path):
	import hashlib
	import subprocess
	import sys

	digests = []
	for run in ("a", "b"):
		out = tmp_path / run
		out.mkdir()
		subprocess.run([sys.executable, str(HERE / "build_tui.py"), str(out)],
		               capture_output=True, check=True, cwd=str(HERE))
		digests.append(hashlib.sha256((out / "bin" / "baton-tui").read_bytes()).hexdigest())
	assert digests[0] == digests[1]


def test_the_cli_artifact_still_has_no_console_in_it():
	"""Re-asserted alongside the trial build, because that is exactly when a
	TUI module would most plausibly leak into the wrong archive."""
	with zipfile.ZipFile(ARTIFACT) as archive:
		names = archive.namelist()
	assert not any("baton_tui" in n or "curses" in n for n in names)


def test_the_core_is_a_library_not_a_runnable_artifact():
	"""`baton-core` is imported, never executed. `baton-tui` is the runnable
	frontend; the agent CLI's adoption of the core is a separate decision that
	nothing here schedules."""
	import subprocess
	import sys

	assert not (HERE / "baton_core" / "__main__.py").exists()
	result = subprocess.run([sys.executable, "-m", "baton_core"],
	                        capture_output=True, text=True, cwd=str(HERE))
	assert result.returncode != 0
	assert "cannot be directly executed" in result.stderr
	# And it exposes no CLI entry point that would make it one by accident.
	sys.path.insert(0, str(HERE))
	import baton_core
	assert not hasattr(baton_core, "main")


def test_the_cli_is_built_from_the_core_and_the_oracle_is_not_shipped():
	"""The explicit decision arrived: stage 1A adopts the core.

	SUPERSEDED, and in exactly one direction. This asserted that `bin/baton`
	contained `baton_v6.py` and no core; it now asserts the reverse. What has
	NOT changed is the reason the test exists — the executable must contain
	one implementation, and it must be obvious which.

	`baton_v6.py` staying OUT of the archive is the load-bearing half. It
	remains in the tree as the differential oracle, and an oracle that ships
	inside the thing it measures has stopped being one."""
	import ast

	with zipfile.ZipFile(ARTIFACT) as archive:
		names = archive.namelist()
	assert any(n.startswith("baton_core/") for n in names), names
	assert "baton_core/_impl.py" in names
	assert "baton_v6.py" not in names, "the frozen oracle is inside the artifact"
	assert not any("baton_tui" in n for n in names)

	# And the oracle still knows nothing about the core, so the two
	# implementations cannot converge by one importing the other.
	source = ast.parse((HERE / "baton_v6.py").read_text())
	for node in ast.walk(source):
		if isinstance(node, ast.Import):
			for alias in node.names:
				assert not alias.name.startswith("baton_core")
		elif isinstance(node, ast.ImportFrom) and node.module:
			assert not node.module.startswith("baton_core")


def test_the_cli_entry_point_is_a_door_not_a_widened_surface():
	"""The CLI needs `main`; a library that exports one invites being run.

	`baton_core.cli` is the single importer, and `import baton_core` still
	gets a library with no `main` on it. Pinned because the tempting shortcut
	-- putting `main` back on the package, or importing `_impl` from the
	bootstrap -- would make a private module part of the distribution contract
	by accident."""
	import sys
	sys.path.insert(0, str(HERE))
	import baton_core
	import baton_core.cli
	assert not hasattr(baton_core, "main"), "the package surface widened"
	assert callable(baton_core.cli.main)

	bootstrap = (HERE / "build_zipapp.py").read_text()
	assert "from baton_core.cli import main" in bootstrap
	assert "from baton_core._impl" not in bootstrap, \
		"the bootstrap reaches into a private module"


def test_the_packaged_cli_publishes_a_tweet(tmp_path):
	"""The ruling asked for the PACKAGED cases, not only the in-process ones.

	The whole reason `--tweet` exists is that the Store contract was
	unreachable from `bin/baton`, so proving it through `main()` alone would
	repeat the mistake at one remove: the artifact is what people run."""
	import json as _json
	import subprocess as _sub
	config = tmp_path / "baton.json"
	config.write_text(_json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "pkg"},
		"participants": {"a.one": {}, "a.two": {}},
		"roots": {}, "retention_days": 90}))
	base = [str(ARTIFACT), "--config", str(config)]
	assert _sub.run(base + ["init"], capture_output=True).returncode == 0

	send = base + ["send", "--participant", "a.one", "--to", "a.two", "--kind", "ping"]
	inline = _sub.run(send + ["--tweet", "ship it when green"], capture_output=True)
	assert inline.returncode == 0, inline.stderr

	piped = _sub.run(send + ["--tweet", "-"], input=b"from a pipe\n", capture_output=True)
	assert piped.returncode == 0, piped.stderr

	crlf = _sub.run(send + ["--tweet", "-"], input=b"crlf line\r\n", capture_output=True)
	assert crlf.returncode == 0, crlf.stderr

	empty = _sub.run(send + ["--tweet", "-"], input=b"", capture_output=True)
	assert empty.returncode != 0 and b"requires text" in empty.stderr

	clash = _sub.run(send + ["--tweet", "x", "--subject", "y"], capture_output=True)
	assert clash.returncode != 0 and b"cannot be combined" in clash.stderr

	notice = _sub.run(base + ["send-notice", "--participant", "a.one",
	                          "--kind", "ann", "--tweet", "no"], capture_output=True)
	assert notice.returncode != 0

	# THE SHARED-LIST OPTION, at the public surface. `--attach` has no
	# namespace attribute -- it collects into the ordered content list -- and
	# the exclusivity check missed it entirely, so this combination exited
	# zero and published a contentless message while discarding the
	# attachment. The executable is where that mattered.
	shared = _sub.run(send + ["--tweet", "x", "--attach", "missing:nowhere"],
	                  capture_output=True)
	assert shared.returncode != 0, shared.stdout
	assert b"cannot be combined with" in shared.stderr
	assert b"--attach" in shared.stderr

	dumped = _sub.run(base + ["dump"], capture_output=True)
	subjects = sorted(m["subject"] for m in _json.loads(dumped.stdout)["messages"])
	assert subjects == ["crlf line", "from a pipe", "ship it when green"]


def test_the_packaged_cli_still_reads_stdin_without_a_tweet(tmp_path):
	"""The preserved behaviour, at the same boundary."""
	import json as _json
	import subprocess as _sub
	config = tmp_path / "baton.json"
	config.write_text(_json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "pkg"},
		"participants": {"a.one": {}, "a.two": {}},
		"roots": {}, "retention_days": 90}))
	base = [str(ARTIFACT), "--config", str(config)]
	assert _sub.run(base + ["init"], capture_output=True).returncode == 0
	sent = _sub.run(base + ["send", "--participant", "a.one", "--to", "a.two",
	                        "--kind", "ping"], input=b"an ordinary body\n",
	                capture_output=True)
	assert sent.returncode == 0, sent.stderr
	empty = _sub.run(base + ["send", "--participant", "a.one", "--to", "a.two",
	                         "--kind", "ping", "--body", "-"], input=b"",
	                 capture_output=True)
	assert empty.returncode != 0 and b"at least one byte" in empty.stderr
