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
import subprocess
import sys

import pytest

SRC = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src")


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
	# R110: ONE packaged build path — the artifact under test is the
	# deployed product, never a second hand-built archive that can
	# drift. (The cli:entry-vs-main lesson from WF-06 is covered by
	# driving the deployed executable's refusal below.)
	staging = tmp_path_factory.mktemp("pack")
	deployer = os.path.join(os.path.dirname(SRC), "tools",
	                        "deploy_work.py")
	target = str(staging / "dist")
	proc = subprocess.run([sys.executable, deployer, target],
	                      capture_output=True, text=True, timeout=300)
	assert proc.returncode == 0, proc.stderr
	return os.path.join(target, "bin", "baton")


def _run(archive_path, authority, *argv, viewer=None, expect_ok=True):
	command = [sys.executable, archive_path, "--config", authority]
	if viewer:
		command += ["--participant", viewer]
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
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import json as _json
	import fixtures as fx
	path = str(tmp_path / "baton.json")
	with open(path, "w") as handle:
		_json.dump(fx.config_document(), handle, indent=2, sort_keys=True)
	_run(archive, path, "activate", f"directory={os.path.dirname(path)}",
	     viewer="lang.ada")

	born = _run(archive, path, "create", "team=web", "kind=bug",
	            "title=render crash", "origin=external-report", "classification=suspected-defect",
	            "body=tab dies", viewer="web.wren")["result"]
	web1, thread = born["work_id"], born["thread"]
	requested = _run(archive, path, "say", f"thread={thread}", "body=yours?",
	                 "request=lang.rsrch", viewer="web.wren")["result"]
	lang_born = _run(archive, path, "create", "team=lang",
	                 "kind=rsrch", "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=dedup",
	                 viewer="lang.ada")["result"]
	lang42, lang_thread = lang_born["work_id"], lang_born["thread"]
	_run(archive, path, "block", f"work={web1}", f"on={lang42}", viewer="web.wren")
	_run(archive, path, "respond", f"obligation={requested["seq"]}",
	     "body=ours, tracked", viewer="lang.ada")
	passed = _run(archive, path, "pass", f"work={lang42}",
	              "to=lang.impl", "phase=active", "set-next=lang.rev", "comment=implement",
	              viewer="lang.ada")["result"]
	assert passed["kind"] == "pass"
	returned = _run(archive, path, "pass", f"work={lang42}",
	                "to=lang.rev", "phase=review", "comment=done",
	                viewer="lang.ada")["result"]
	assert returned["kind"] == "return"
	_run(archive, path, "close", f"work={lang42}", "rationale=verified", "outcome=satisfying",
	     viewer="lang.ada")
	after = _run(archive, path, "detail", f"work={web1}", viewer="web.wren")["result"]
	assert after["ready"] is True

	events = _run(archive, path, "events",
	              viewer="lang.ada")["result"]
	seqs = [event["seq"] for event in events]
	assert seqs == list(range(1, len(seqs) + 1))
	assert [event["kind"] for event in events][-6:] == \
		["create_work", "add_dependency", "respond", "pass", "return",
		 "close_work"]


def test_a_refusal_exits_nonzero_through_the_archive(archive, tmp_path):
	"""From WF-06's cycle-refusal checkpoint (workflow-to-regression rule):
	the refusal printed its structured error but the ARCHIVE exited 0,
	because zipapp's __main__ calls the target and discards its return
	value. The exit status is part of the refusal: a scripted caller that
	cannot see it will treat every refused operation as having happened."""
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import json as _json
	import fixtures as fx
	path = str(tmp_path / "baton.json")
	with open(path, "w") as handle:
		_json.dump(fx.config_document(), handle, indent=2, sort_keys=True)
	_run(archive, path, "activate", f"directory={os.path.dirname(path)}",
	     viewer="lang.ada")
	refusal = _run(archive, path, "create", "team=lang",
	               "kind=nope", "title=x",
	               "origin=external-report", "classification=suspected-defect", "body=x", viewer="lang.ada",
	               expect_ok=False)
	assert "not a registered endpoint" in refusal["error"] or \
		"not a configured endpoint" in refusal["error"]


def test_the_archive_answers_without_the_source_tree(archive, tmp_path):
	"""The property, stated directly: a poisoned lookalike package on the
	path must not be what the archive runs."""
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import json as _json
	import fixtures as fx
	path = str(tmp_path / "baton.json")
	with open(path, "w") as handle:
		_json.dump(fx.config_document(), handle, indent=2, sort_keys=True)
	poison = tmp_path / "poison" / "baton_work"
	poison.mkdir(parents=True)
	(poison / "__init__.py").write_text("raise RuntimeError('poisoned')\n")
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}
	env["PYTHONPATH"] = str(tmp_path / "poison")
	proc = subprocess.run(
		[sys.executable, archive, "--config", path,
		 "--participant", "lang.ada", "activate",
		 f"directory={os.path.dirname(path)}"],
		capture_output=True, text=True, timeout=120, env=env)
	assert proc.returncode == 0, \
		"the archive deferred to a poisoned path package: " + proc.stderr
	assert json.loads(proc.stdout)["result"]["generation"] == 1
