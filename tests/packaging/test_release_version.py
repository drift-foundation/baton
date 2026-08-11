"""One release version, reported by both executables, offline.

The pre-release numbers drifted on purpose -- the CLI counted its own tool
revisions to 6.0.0 while the console sat at 0.2.0 -- and that is exactly what
a public release cannot ship: two numbers for one thing, with nothing saying
which one a human should quote. These tests pin the single declaration and
every surface that repeats it, because a version string is only useful if the
source, the packaged bytes, the manifests, and the documentation cannot
disagree.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import baton_core

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "src"
TOOLS = REPO / "tools"
DIST = REPO / "dist"
CLI = REPO / "bin" / "baton"
TUI = REPO / "bin" / "baton-tui"

RELEASE = baton_core.RELEASE_VERSION
PROTOCOL = baton_core.PROTOCOL_VERSION

CLI_LINE = f"baton {RELEASE} (protocol {PROTOCOL})"
TUI_LINE = f"baton-tui {RELEASE} (protocol {PROTOCOL})"


def test_the_release_version_is_a_single_semantic_declaration():
	"""`major.minor.patch`, declared once.

	The literal `1.0.0` is asserted here and nowhere else in this file: every
	other test derives from `baton_core.RELEASE_VERSION`, so a future release
	changes one constant and this one test, instead of a scatter of strings
	that each have to be found."""
	assert RELEASE == "1.0.0"
	parts = RELEASE.split(".")
	assert len(parts) == 3 and all(p.isdigit() for p in parts), RELEASE

	# The console must not carry a product version of its own. This is the
	# drift the ruling closed, so its absence is the assertion.
	import baton_tui
	assert not hasattr(baton_tui, "TUI_VERSION")
	assert not hasattr(baton_core, "TOOL_VERSION")


def test_both_source_parsers_answer_version_and_advertise_it_in_help():
	"""Evidence 1: the argument surface, before any packaging."""
	import contextlib
	import io

	from baton_core import _impl
	from baton_tui.driver import build_parser

	for parser, expected in ((_impl._build_parser(), CLI_LINE),
	                         (build_parser(), TUI_LINE)):
		# What argparse actually PRINTS, not what the action was configured
		# with: the configured string can be right while the wiring is not.
		out = io.StringIO()
		try:
			with contextlib.redirect_stdout(out):
				parser.parse_args(["--version"])
		except SystemExit as exit_:
			assert exit_.code == 0
		else:                                          # pragma: no cover
			raise AssertionError("--version did not exit")
		assert out.getvalue() == expected + "\n", out.getvalue()

		help_text = parser.format_help()
		assert "--version" in help_text
		assert "print the release version and exit" in help_text


def test_the_console_answers_version_before_its_required_arguments():
	"""`--config` and `--participant` are `required=True`.

	A version query that demanded them would satisfy the letter of "prints a
	version" and none of the point: the ruling says no config and no
	participant. `--help` is checked the same way, since it exits through the
	same path."""
	from baton_tui.driver import build_parser

	for flag in ("--version", "--help"):
		try:
			build_parser().parse_args([flag])
		except SystemExit as exit_:
			assert exit_.code == 0, flag
		else:                                          # pragma: no cover
			raise AssertionError(f"{flag} did not exit")

	# The required arguments are still required for an ordinary run.
	try:
		build_parser().parse_args([])
	except SystemExit as exit_:
		assert exit_.code != 0
	else:                                              # pragma: no cover
		raise AssertionError("missing required arguments were accepted")


def _offline_run(argv, cwd):
	"""Run an executable with the environment a version query must not need.

	`HOME` is redirected and every `BATON_*` variable is dropped, so anything
	the query reached for by convention rather than by argument shows up as a
	failure instead of silently working on the developer's own machine."""
	env = {k: v for k, v in os.environ.items() if not k.startswith("BATON_")}
	env["HOME"] = str(cwd)
	env.pop("TERM", None)
	return subprocess.run(argv, capture_output=True, cwd=str(cwd), env=env)


def test_both_packaged_executables_print_the_ruled_line(tmp_path):
	"""Evidence 2: the artifacts, not the source tree.

	No config, no terminal (`TERM` removed and the pipes are not a tty), no
	participant, no authority, no project directory -- an empty temporary
	directory is the whole world. Exactly one line, exit zero."""
	for artifact, expected in ((CLI, CLI_LINE), (TUI, TUI_LINE)):
		run = _offline_run([str(artifact), "--version"], tmp_path)
		assert run.returncode == 0, (artifact.name, run.stderr)
		assert run.stdout.decode() == expected + "\n", run.stdout
		assert run.stderr == b"", run.stderr


def test_the_version_query_touches_no_store_config_or_project(tmp_path):
	"""Evidence 3: the tripwire.

	Three ways for the query to be doing more than it says: leaving something
	behind, reading a config, or refusing without one. A version query that
	created a store would pass the output test above and still be wrong."""
	for artifact, expected in ((CLI, CLI_LINE), (TUI, TUI_LINE)):
		home = tmp_path / f"home-{artifact.name}"
		home.mkdir()

		run = _offline_run([str(artifact), "--version"], home)
		assert run.returncode == 0, run.stderr
		# Nothing written: no store, no journal, no dotfile, no lock.
		assert sorted(p.name for p in home.iterdir()) == [], \
			sorted(p.name for p in home.iterdir())

		# A config path that does not exist must not even be looked at.
		missing = str(home / "nowhere" / "baton.json")
		named = _offline_run([str(artifact), "--config", missing, "--version"], home)
		assert named.returncode == 0, named.stderr
		assert named.stdout.decode() == expected + "\n"
		assert sorted(p.name for p in home.iterdir()) == []


def test_both_manifests_and_the_readme_agree_with_the_source(tmp_path):
	"""Evidence 4: no surface may hold its own copy of the number."""
	cli_manifest = json.loads((DIST / "DISTRIBUTION.json").read_text())
	tui_manifest = json.loads((DIST / "DISTRIBUTION-TUI.json").read_text())

	# The SAME key in both, so agreement is checkable rather than inferred.
	assert cli_manifest["release_version"] == RELEASE
	assert tui_manifest["release_version"] == RELEASE
	assert cli_manifest["protocol_version"] == PROTOCOL
	assert tui_manifest["protocol_version"] == PROTOCOL
	# The retired per-artifact versions must not linger beside the shared one.
	assert "tool_version" not in cli_manifest
	assert "tui_version" not in tui_manifest

	readme = (REPO / "README.md").read_text()
	assert CLI_LINE in readme, CLI_LINE
	assert TUI_LINE in readme, TUI_LINE


def test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests(tmp_path):
	"""Evidence 5: the bytes in `bin/` are the bytes this source builds.

	Built into a scratch root so the checked-in artifacts are read, never
	rewritten, by a test."""
	import hashlib

	root = tmp_path / "root"
	root.mkdir()
	for builder in ("build_zipapp.py", "build_tui.py"):
		built = subprocess.run([sys.executable, str(TOOLS / builder), str(root)],
		                       capture_output=True)
		assert built.returncode == 0, (builder, built.stderr)

	for name, checked_in in (("DISTRIBUTION.json", CLI),
	                         ("DISTRIBUTION-TUI.json", TUI)):
		manifest = json.loads((root / "dist" / name).read_text())
		assert manifest["release_version"] == RELEASE
		rebuilt = root / manifest["artifact"]
		assert hashlib.sha256(rebuilt.read_bytes()).hexdigest() == \
			manifest["artifact_sha256"]
		assert rebuilt.read_bytes() == checked_in.read_bytes(), manifest["artifact"]

		published = json.loads((DIST / name).read_text())
		assert published == manifest, name
