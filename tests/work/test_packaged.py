"""B3: the ruled scenario through a PACKAGED artifact, not the source tree.

v11 has no entry in the release catalog yet — that is deliberate release
work outside this gate — so the packaged artifact is built HERE, by the
stdlib `zipapp` machinery, from the same sources, and the scenario runs
through the archive with the source tree deliberately ABSENT from the
child's path. What this proves is the packaging property that bit the v10
console once already: the code works when entered through an archive, with
no help from the checkout.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipapp

import pytest

SRC = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src")


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
	staging = tmp_path_factory.mktemp("pack")
	shutil.copytree(os.path.join(SRC, "baton_work"),
	                str(staging / "app" / "baton_work"))
	target = str(staging / "baton-work.pyz")
	zipapp.create_archive(str(staging / "app"), target,
	                      interpreter=None, main="baton_work.cli:main")
	return target


def _run(archive_path, authority, *argv, viewer=None, expect_ok=True):
	command = [sys.executable, archive_path, "--authority", authority]
	if viewer:
		command += ["--viewer", viewer]
	command += list(argv)
	# NO PYTHONPATH: the archive answers alone or the test fails.
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}
	proc = subprocess.run(command, capture_output=True, text=True,
	                      timeout=120, env=env)
	if expect_ok:
		assert proc.returncode == 0, proc.stderr or proc.stdout
		return json.loads(proc.stdout)
	assert proc.returncode == 1, proc.stdout
	return json.loads(proc.stderr)


def test_the_gate_scenario_through_the_archive(archive, tmp_path):
	path = str(tmp_path / "work.sqlite3")
	_run(archive, path, "init")
	for team, member in (("lang", "ada"), ("web", "wren")):
		_run(archive, path, "register-team", "--team", team,
		     "--display", team.title())
		_run(archive, path, "register-member", "--team", team,
		     "--member", member, "--display", member.title())
	_run(archive, path, "register-kind", "--team", "web", "--kind", "bug",
	     "--display", "Bug intake")
	for kind in ("rsrch", "impl", "rev"):
		_run(archive, path, "register-kind", "--team", "lang",
		     "--kind", kind, "--display", kind)

	web1 = _run(archive, path, "create", "--team", "web", "--kind", "bug",
	            "--title", "render crash", "--origin", "external-report",
	            "--body", "tab dies", viewer="web.wren")["result"]["work_id"]
	requested = _run(archive, path, "post", web1, "--body", "yours?",
	                 "--request", "lang.rsrch", viewer="web.wren")["result"]
	lang42 = _run(archive, path, "create", "--team", "lang",
	              "--kind", "rsrch", "--title", "parser recovery",
	              "--origin", "external-report", "--body", "dedup",
	              viewer="lang.ada")["result"]["work_id"]
	_run(archive, path, "block", web1, "--on", lang42, viewer="web.wren")
	_run(archive, path, "respond", str(requested["seq"]),
	     "--body", "ours, tracked", viewer="lang.ada")
	passed = _run(archive, path, "post", lang42, "--body", "implement",
	              "--pass-to", "lang.impl", "--set-next", "lang.rev",
	              viewer="lang.ada")["result"]
	assert passed["kind"] == "pass"
	returned = _run(archive, path, "post", lang42, "--body", "done",
	                "--pass-to", "lang.rev", viewer="lang.ada")["result"]
	assert returned["kind"] == "return"
	_run(archive, path, "close", lang42, "--disposition", "verified",
	     viewer="lang.ada")
	after = _run(archive, path, "detail", web1, viewer="web.wren")["result"]
	assert after["ready"] is True

	events = _run(archive, path, "events")["result"]
	seqs = [event["seq"] for event in events]
	assert seqs == list(range(1, len(seqs) + 1))
	assert [event["kind"] for event in events][-6:] == \
		["create_work", "add_dependency", "respond", "pass", "return",
		 "close_work"]


def test_the_archive_answers_without_the_source_tree(archive, tmp_path):
	"""The property, stated directly: a poisoned lookalike package on the
	path must not be what the archive runs."""
	path = str(tmp_path / "work.sqlite3")
	poison = tmp_path / "poison" / "baton_work"
	poison.mkdir(parents=True)
	(poison / "__init__.py").write_text("raise RuntimeError('poisoned')\n")
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}
	env["PYTHONPATH"] = str(tmp_path / "poison")
	proc = subprocess.run(
		[sys.executable, archive, "--authority", path, "init"],
		capture_output=True, text=True, timeout=120, env=env)
	assert proc.returncode == 0, \
		"the archive deferred to a poisoned path package: " + proc.stderr
	assert json.loads(proc.stdout)["result"] == {"initialized": True}
