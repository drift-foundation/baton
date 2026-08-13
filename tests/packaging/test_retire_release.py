"""R39: the production repair, rehearsed adversarially.

The PLAN 25 repair was first written as `chmod -R u+w` and `rm -rf` over paths
under `/home/sl/baton`. This file exists because those commands have no failure
mode that is not catastrophic, and because a runbook step nobody can test is a
step nobody reviewed.

EVERY TEST HERE TRIES TO MAKE IT DELETE THE WRONG THING. A tool whose happy
path works proves nothing about the 2am case; what has to be pinned is that it
refuses a swapped ancestor, a path that escapes, a release with something
unexplained inside it, and a release the alias still names — and that after
each refusal the tree is exactly as it was.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"tools"))

import candidate                                              # noqa: E402
import deploy                                                 # noqa: E402
import retire_release                                         # noqa: E402


def _tree(root: pathlib.Path) -> dict:
	"""Every path under `root`, with its bytes' digest. The witness."""
	seen = {}
	for path in sorted(root.rglob("*")):
		relative = str(path.relative_to(root))
		if path.is_symlink():
			seen[relative] = "link:" + os.readlink(path)
		elif path.is_dir():
			seen[relative] = "dir"
		else:
			seen[relative] = deploy.digest(str(path))
	return seen


@pytest.fixture
def deployed(tmp_path):
	"""A real installed release, from the real candidate."""
	candidate.require()
	destination = tmp_path / "dest"
	result = deploy.install(str(candidate.ROOT), str(destination))
	version = json.loads(
		(candidate.DIST / "DISTRIBUTION.json").read_text())["product_version"]
	return destination, f"v{version}", f"v{version.split('.')[0]}"


# -- the happy path, stated once so the refusals mean something --------------

def test_a_planned_retirement_names_every_path_before_touching_any(deployed):
	destination, release, namespace = deployed
	before = _tree(destination)

	plan = retire_release.plan_retire(str(destination), "baton-cli",
	                                  namespace, release)
	# The alias still points at it, so this is a refusal -- and a PLAN is still
	# produced, because "what is wrong" is what an operator needs.
	assert any("still points at" in problem for problem in plan["refusals"])
	assert _tree(destination) == before, "planning wrote something"

	dropped = retire_release.drop_alias(str(destination), "baton-cli",
	                                    namespace, apply=True)
	assert dropped["target"] == release

	plan = retire_release.plan_retire(str(destination), "baton-cli",
	                                  namespace, release)
	assert plan["refusals"] == []
	paths = {item["path"] for item in plan["removals"]}
	assert f"{namespace}/{release}/PRODUCT.json" in paths
	assert f"{namespace}/{release}/bin/baton" in paths
	assert any(item.get("sha256") for item in plan["removals"])
	# Dropping the alias removed exactly one path and nothing else.
	assert set(before) - set(_tree(destination)) == \
		{f"app/baton-cli/{namespace}/latest"}

	# A DRY RUN CHANGES NOTHING.
	after_plan = _tree(destination)
	assert retire_release.retire(str(destination), "baton-cli", namespace,
	                             release)["applied"] is False
	assert _tree(destination) == after_plan

	report = retire_release.retire(str(destination), "baton-cli", namespace,
	                               release, apply=True)
	assert report["applied"] is True
	assert not (destination / "app" / "baton-cli" / namespace / release).exists()
	# ...and it removed ONLY that release: the other product is untouched.
	assert (destination / "app" / "baton-tui" / namespace / release).is_dir()
	assert (destination / "operations").is_dir()


# -- every way to make it delete the wrong thing ------------------------------

@pytest.mark.parametrize("product,namespace,release,fragment", [
	("baton-cli", "v10", "..", "not an exact release"),
	("baton-cli", "v10", "v10", "not an exact release"),
	("baton-cli", "v10", "v10.2.0/../../..", "not an exact release"),
	("baton-cli", "v10", "*", "not an exact release"),
	("baton-cli", "..", "v10.2.0", "not a generation name"),
	("baton-cli", "v10/../..", "v10.2.0", "not a generation name"),
	("../../etc", "v10", "v10.2.0", "not a product directory"),
	("baton-cli.old", "v10", "v10.2.0", "not a product directory"),
])
def test_a_component_that_is_not_a_validated_name_is_refused(tmp_path, product,
                                                             namespace,
                                                             release,
                                                             fragment):
	"""No path this tool composes is free text. `rm -rf "$DEST/app/$P/$N/$R"`
	would have expanded every one of these."""
	with pytest.raises(retire_release.RetireError, match=fragment):
		retire_release.plan_retire(str(tmp_path), product, namespace, release)


def test_a_symlinked_generation_directory_is_refused(deployed):
	"""The ancestor swap. `rm -rf` follows a directory symlink's contents
	happily; every component here is opened `O_NOFOLLOW`."""
	destination, release, namespace = deployed
	elsewhere = destination.parent / "elsewhere"
	(elsewhere / release).mkdir(parents=True)
	(elsewhere / release / "PRODUCT.json").write_text("{}")
	before = _tree(elsewhere)

	product_dir = destination / "app" / "baton-cli"
	real = product_dir / namespace
	os.rename(real, product_dir / "moved-away")
	os.symlink(elsewhere, real)

	with pytest.raises(retire_release.RetireError, match="symlink|not a directory"):
		retire_release.plan_retire(str(destination), "baton-cli", namespace,
		                           release)
	assert _tree(elsewhere) == before, "it reached through the link"


def test_a_symlinked_root_is_refused(deployed):
	destination, release, namespace = deployed
	link = destination.parent / "as-a-link"
	os.symlink(destination, link)
	with pytest.raises(deploy.DeployError, match="symlink"):
		retire_release.plan_retire(str(link), "baton-cli", namespace, release)


def test_a_release_holding_something_unexplained_is_refused(deployed):
	"""The reason a bounded shape matters. An unrecognised file is either
	evidence or a sign this is not the directory we think it is; deleting it
	on the way past answers neither question."""
	destination, release, namespace = deployed
	retire_release.drop_alias(str(destination), "baton-cli", namespace,
	                          apply=True)
	release_dir = destination / "app" / "baton-cli" / namespace / release
	release_dir.chmod(0o755)
	(release_dir / "operator-notes.txt").write_text("read me first\n")
	before = _tree(destination)

	plan = retire_release.plan_retire(str(destination), "baton-cli", namespace,
	                                  release)
	assert any("operator-notes.txt" in problem for problem in plan["refusals"])
	with pytest.raises(retire_release.RetireError, match="operator-notes"):
		retire_release.retire(str(destination), "baton-cli", namespace,
		                      release, apply=True)
	assert _tree(destination) == before


def test_a_member_replaced_by_a_symlink_is_refused(deployed):
	"""The classic: `bin` becomes a link to somewhere that matters."""
	destination, release, namespace = deployed
	retire_release.drop_alias(str(destination), "baton-cli", namespace,
	                          apply=True)
	victim = destination.parent / "victim"
	victim.mkdir()
	(victim / "precious").write_text("do not delete\n")

	release_dir = destination / "app" / "baton-cli" / namespace / release
	release_dir.chmod(0o755)
	bin_dir = release_dir / "bin"
	bin_dir.chmod(0o755)
	(bin_dir / "baton").chmod(0o644)
	(bin_dir / "baton").unlink()
	bin_dir.rmdir()
	os.symlink(victim, bin_dir)

	plan = retire_release.plan_retire(str(destination), "baton-cli", namespace,
	                                  release)
	assert any("symlink" in problem for problem in plan["refusals"])
	with pytest.raises(retire_release.RetireError, match="symlink"):
		retire_release.retire(str(destination), "baton-cli", namespace,
		                      release, apply=True)
	assert (victim / "precious").read_text() == "do not delete\n"


def test_a_release_the_alias_still_names_is_refused(deployed):
	"""Order is part of the act: dropping the alias is its own decision,
	because it is the moment nothing is discoverable."""
	destination, release, namespace = deployed
	before = _tree(destination)
	with pytest.raises(retire_release.RetireError, match="still points at"):
		retire_release.retire(str(destination), "baton-cli", namespace,
		                      release, apply=True)
	assert _tree(destination) == before


def test_a_release_that_changed_after_planning_is_not_removed(deployed,
                                                              monkeypatch):
	"""A stale plan is exactly as dangerous as a hand-composed path: the tool
	re-reads the directory and compares before it unlinks anything."""
	destination, release, namespace = deployed
	retire_release.drop_alias(str(destination), "baton-cli", namespace,
	                          apply=True)
	release_dir = destination / "app" / "baton-cli" / namespace / release

	real_plan = retire_release.plan_retire

	def plan_then_meddle(*args, **kwargs):
		report = real_plan(*args, **kwargs)
		release_dir.chmod(0o755)
		(release_dir / "appeared-after-planning").write_text("late\n")
		return report

	monkeypatch.setattr(retire_release, "plan_retire", plan_then_meddle)
	with pytest.raises(retire_release.RetireError, match="changed since"):
		retire_release.retire(str(destination), "baton-cli", namespace,
		                      release, apply=True)
	assert (release_dir / "appeared-after-planning").is_file()
	assert (release_dir / "PRODUCT.json").is_file(), "it removed part of it"


# -- flattening the frozen pair ----------------------------------------------

@pytest.fixture
def frozen(tmp_path):
	"""The shape Checkpoint A left in production: a hand-made version
	directory holding only `bin/`, with no record and no alias."""
	home = tmp_path / "dest" / "app" / "baton-cli" / "legacy" / "v1.1.0" / "bin"
	home.mkdir(parents=True)
	(home / "baton").write_bytes(b"#!/usr/bin/env python3\n# frozen\n")
	(home / "baton").chmod(0o755)
	return tmp_path / "dest"


def test_flattening_moves_the_bytes_and_removes_the_empty_directory(frozen):
	before = deploy.digest(str(frozen / "app" / "baton-cli" / "legacy"
	                           / "v1.1.0" / "bin" / "baton"))

	dry = retire_release.flatten(str(frozen), "baton-cli", "legacy", "v1.1.0",
	                             artifact="baton")
	assert dry["applied"] is False
	assert dry["sha256"] == before
	assert (frozen / "app" / "baton-cli" / "legacy" / "v1.1.0").is_dir()

	report = retire_release.flatten(str(frozen), "baton-cli", "legacy",
	                                "v1.1.0", artifact="baton", apply=True)
	assert report["applied"] is True
	moved = frozen / "app" / "baton-cli" / "legacy" / "bin" / "baton"
	assert deploy.digest(str(moved)) == before
	assert not (frozen / "app" / "baton-cli" / "legacy" / "v1.1.0").exists()
	assert os.access(moved, os.X_OK), "the frozen binary stopped being runnable"


def test_flattening_refuses_to_overwrite_an_existing_bin(frozen):
	"""The one thing it must never do."""
	existing = frozen / "app" / "baton-cli" / "legacy" / "bin"
	existing.mkdir()
	(existing / "baton").write_bytes(b"the real one\n")

	with pytest.raises(retire_release.RetireError, match="already exists"):
		retire_release.flatten(str(frozen), "baton-cli", "legacy", "v1.1.0",
		                       artifact="baton", apply=True)
	assert (existing / "baton").read_bytes() == b"the real one\n"


def test_flattening_refuses_an_installed_release(deployed):
	"""An installed release has `doc/`, `conf/` and a record. Flattening one
	would silently discard them; `retire` is the act for a release."""
	destination, release, namespace = deployed
	with pytest.raises(retire_release.RetireError, match="not just"):
		retire_release.flatten(str(destination), "baton-cli", namespace,
		                       release, artifact="baton", apply=True)
	assert (destination / "app" / "baton-cli" / namespace / release
	        / "PRODUCT.json").is_file()


def test_flattening_refuses_a_bin_holding_more_than_the_artifact(frozen):
	extra = frozen / "app" / "baton-cli" / "legacy" / "v1.1.0" / "bin"
	(extra / "baton-tui").write_bytes(b"the other product\n")
	with pytest.raises(retire_release.RetireError, match="not exactly"):
		retire_release.flatten(str(frozen), "baton-cli", "legacy", "v1.1.0",
		                       artifact="baton", apply=True)
	assert (extra / "baton").is_file() and (extra / "baton-tui").is_file()


@pytest.mark.parametrize("artifact", ["../baton", "bin/baton", ".hidden"])
def test_flattening_refuses_an_artifact_name_that_is_a_path(frozen, artifact):
	with pytest.raises(retire_release.RetireError, match="bare artifact name"):
		retire_release.flatten(str(frozen), "baton-cli", "legacy", "v1.1.0",
		                       artifact=artifact, apply=True)


# -- the command line is the thing an operator actually types -----------------

def test_the_command_line_is_dry_unless_it_is_told_otherwise(deployed, capsys):
	destination, release, namespace = deployed
	before = _tree(destination)
	code = retire_release.main(["drop-alias", str(destination),
	                            "--product", "baton-cli",
	                            "--namespace", namespace])
	assert code == 0
	report = json.loads(capsys.readouterr().out)
	assert report["applied"] is False and report["target"] == release
	assert _tree(destination) == before


def test_the_command_line_reports_refusals_as_a_nonzero_exit(deployed, capsys):
	destination, release, namespace = deployed
	code = retire_release.main(["plan", str(destination),
	                            "--product", "baton-cli",
	                            "--namespace", namespace,
	                            "--release", release])
	assert code == 1
	assert "still points at" in capsys.readouterr().out
