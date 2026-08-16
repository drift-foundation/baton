"""C3: the configuration boundary at the public CLI surface.

The launch contract, tested as a contract: --config/--participant are the
whole identity surface, the removed verbs are refusals rather than aliases,
every ordinary command validates the participant BEFORE output, and regen is
accept_config wearing its CLI name with the capability gate intact.
"""

from __future__ import annotations

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

from baton_work import cli                                    # noqa: E402
import fixtures                                               # noqa: E402


@pytest.fixture
def instance(tmp_path):
	config_path, _db = fixtures.build_instance(str(tmp_path))
	return config_path


def _run(capsys, config, *argv, participant=None, expect_ok=True):
	args = ["--config", config]
	if participant:
		args += ["--participant", participant]
	code = cli.main(args + list(argv))
	captured = capsys.readouterr()
	if expect_ok:
		assert code == 0, captured.err
		return json.loads(captured.out)
	assert code == 1, captured.out
	return json.loads(captured.err)


def test_the_removed_registry_verbs_are_gone_not_aliased(instance, capsys):
	# Slice B: the whole Work-addressed thread/operator bridge is
	# gone from the packaged parser — `post WORK` included. No
	# compatibility alias remains.
	for verb in ("register-team", "register-member", "register-kind",
	             "retire-kind", "post"):
		code = cli.main(["--config", instance, verb])
		captured = capsys.readouterr()
		assert code == 1, f"{verb} still parses"
		assert "unknown command" in captured.err
	for flag in ("--authority", "--viewer"):
		code = cli.main([flag, "x", "home"])
		captured = capsys.readouterr()
		assert code == 1, f"{flag} still parses"
		assert "launcher context" in captured.err


def test_an_unknown_participant_refuses_before_any_output(instance, capsys):
	error = _run(capsys, instance, "home", participant="ghost.gone",
	             expect_ok=False)
	assert "not a participant of the accepted configuration" in error["error"]
	error = _run(capsys, instance, "say", "thread=some-thread", "body=x",
	             participant="lang.nope", expect_ok=False)
	assert "not a participant" in error["error"]


def test_an_edited_config_refuses_every_ordinary_command(instance, capsys):
	document = fixtures.config_document()
	document["teams"]["web"]["display"] = "Edited"
	with open(instance, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	error = _run(capsys, instance, "home", participant="lang.ada",
	             expect_ok=False)
	assert "edited but not accepted" in error["error"]


def test_regen_accepts_a_generation_plus_one_under_the_capability(instance,
                                                                  capsys):
	document = fixtures.config_document()
	document["generation"] = 2
	document["teams"]["web"]["display"] = "Web Platform"
	with open(instance, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)

	# grace holds no config capability: refused.
	error = _run(capsys, instance, "regen", participant="lang.grace",
	             expect_ok=False)
	assert "cannot authorize its own acceptor" in error["error"] or \
		"does not hold the config capability" in error["error"]
	# ada holds it: accepted, and ordinary opens work again.
	result = _run(capsys, instance, "regen",
	              participant="lang.ada")["result"]
	assert result["generation"] == 2
	home = _run(capsys, instance, "home", participant="lang.ada")
	assert home["snapshot_seq"] >= 2


def test_regen_requires_a_participant(instance, capsys):
	error = _run(capsys, instance, "regen", expect_ok=False)
	assert "needs --participant" in error["error"]


def test_init_reports_the_binding(tmp_path, capsys):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		json.dump(fixtures.config_document(), handle, indent=2,
		          sort_keys=True)
	result = _run(capsys, config_path, "activate",
	              f"directory={os.path.dirname(config_path)}",
	              participant="lang.ada")["result"]
	assert result["generation"] == 1
	assert result["authority_uuid"] == fixtures.UUID
	assert result["database"].endswith("work.sqlite3")


def test_every_ordinary_read_requires_a_participant(instance, capsys):
	"""C3 review R1: links/breadcrumb/thread/events were anonymous —
	an identity-by-assertion defect wearing a read-only disguise. Every
	non-init command now refuses without --participant."""
	for argv in (("links", "work=w"), ("breadcrumb", "work=w"), ("thread", "thread=w"),
	             ("events",), ("home",), ("obligations",)):
		error = _run(capsys, instance, *argv, expect_ok=False)
		assert "needs --participant" in error["error"], argv


def test_the_public_grammar_accepts_full_spellings_only(tmp_path):
	"""R117: long-option abbreviation is disabled — `--part` is not
	`--participant` anywhere on the public surface, so no identity or
	configuration global can be smuggled through a prefix."""
	import subprocess
	import sys as _sys
	import fixtures as fx
	config_path, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]}})
	src = os.path.join(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))), "src")
	env = dict(os.environ, PYTHONPATH=src)
	proc = subprocess.run(
		[_sys.executable, "-m", "baton_work.cli",
		 "--config", config_path, "--part", "lang.ada", "home"],
		capture_output=True, text=True, timeout=120, env=env)
	assert proc.returncode != 0, \
		"an abbreviated global was accepted by the public grammar"
	assert "--part" in proc.stderr
