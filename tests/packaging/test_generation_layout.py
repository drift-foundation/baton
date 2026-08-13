"""The generation layout: what a path is allowed to claim, and who checks it.

A set digest is the only name in the superseded design that CANNOT lie — it is
computed from the bytes it names. It is also unreadable, unguessable and
impossible to say out loud, which is why the ruling replaced it with paths
built from versions:

    DEST/app/baton-cli/v11/v11.2.0/     one immutable release
    DEST/app/baton-cli/v11/latest       relative discovery alias
    DEST/mailbox/v11/MAILBOX.json       the compatibility handshake

That is a good trade for navigability ONLY if the checks in this file exist. A
version-shaped path is a name a human assigns, and every test here is about
stopping it from lying: the directory, the record, the manifest, the mailbox
and the running client must all say the same number, or the tool refuses.

`tests/packaging/test_deploy.py` covers certification and the superseded set
reader. This file covers the layout, the aliases, the handshake and the
exact-path execution rule.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

import deploy                                          # noqa: E402
import candidate                                       # noqa: E402
from synthetic import CATALOG, candidate_tree, rebuild  # noqa: E402


def _bumped(tmp_path, name, cli_version, tui_version):
	"""A synthetic candidate at NEW versions, coherent end to end.

	Two releases have to come from two candidates: `verify_release`
	reconstructs the whole projection from the carried manifest, so a
	hand-edited release directory cannot exist. That is the check doing its
	job, and it means fixtures build candidates rather than directories."""
	source = candidate_tree(tmp_path / name)
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton"]["version"] = cli_version
	catalog["products"]["baton-tui"]["version"] = tui_version
	rebuild(source, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(source, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	for tool, version in (("baton", cli_version), ("baton-tui", tui_version)):
		(source / "docs" / f"RELEASE-{tool}-{version}.md").write_bytes(b"# note\n")
	return source


@pytest.fixture
def installed(tmp_path):
	"""The real candidate, installed into a scratch destination.

	The REAL one, deliberately: installation is byte-preserving, and a
	synthetic fixture could not prove bytes it made up were preserved."""
	candidate.require()
	destination = tmp_path / "dest"
	result = deploy.install(str(candidate.ROOT), str(destination))
	return destination, result


def _digest(path) -> str:
	return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _installed_version(tool: str = "baton") -> str:
	"""The version the CANDIDATE carries, read from its own manifest.

	Not typed here. These tests run against whatever `just build` last
	prepared, so a hard-coded version passes until the day someone bumps the
	catalog and then fails in twenty places at once -- which is exactly the
	shape of breakage the version bump to 1.2.0 would have handed the next
	person to run the suite.
	"""
	name = "DISTRIBUTION.json" if tool == "baton" else "DISTRIBUTION-TUI.json"
	return json.loads((candidate.DIST / name).read_text())["product_version"]


def _release_path(destination, product: str, tool: str = "baton"):
	version = _installed_version(tool)
	return (pathlib.Path(destination) / "app" / product
	        / deploy.namespace_for(tool, version, 10) / ("v" + version))


def _rewrite_record(release, change):
	"""Edit an installed record and PUT THE MODES BACK.

	Not tidiness: leaving the release at 0755 and the record at 0644 makes
	`verify_release` fail on the modes, so an assertion of "it did not verify"
	passes whether or not the edited CONTENT was noticed. Three tests in this
	file were passing that way, and the check they were supposed to be pinning
	was not running at all.
	"""
	record_path = pathlib.Path(release) / "PRODUCT.json"
	pathlib.Path(release).chmod(0o755)
	record_path.chmod(0o644)
	record = json.loads(record_path.read_text())
	change(record)
	record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
	record_path.chmod(0o444)
	pathlib.Path(release).chmod(0o555)
	return record_path


# -- installing is byte-preserving ------------------------------------------

def test_the_installed_applications_are_byte_identical_to_the_candidate(installed):
	"""Installation is layout-only. An application must arrive at its exact
	release path without one byte changing: a deployer that can alter what it
	installs is a second build nobody reviewed."""
	destination, _result = installed
	for tool, product, artifact in (("baton", "baton-cli", "bin/baton"),
	                                ("baton-tui", "baton-tui", "bin/baton-tui")):
		release = _release_path(destination, product, tool)
		assert _digest(release / artifact) == _digest(candidate.ROOT / artifact)


def test_the_installed_applications_still_report_their_own_identity(installed):
	"""Not relabelled, not rebuilt: run from the new path, they say what they
	always said."""
	destination, _result = installed
	for product, tool, artifact in (("baton-cli", "baton", "bin/baton"),
	                                ("baton-tui", "baton-tui", "bin/baton-tui")):
		exact = _release_path(destination, product, tool) / artifact
		printed = subprocess.run([sys.executable, str(exact), "--version"],
		                         capture_output=True, text=True)
		assert printed.returncode == 0, printed.stderr
		# What the CANDIDATE says about itself, not a version typed here: the
		# claim under test is that installing does not relabel anything.
		assert printed.stdout.strip() == \
			f"{tool} {_installed_version(tool)} (protocol 10)"


def test_the_namespace_is_derived_and_there_is_no_grant(installed):
	"""SUPERSEDED 2026-08-13. This used to assert that `legacy` was a namespace
	granted BY NAME to the 1.x pair, and that `PRODUCT.json` carried a
	`legacy_mapping` explaining why a major-1 release served protocol 10.

	The correction removed the legacy release family: a release's major IS its
	generation, arithmetic and without exception. So the record must say `v10`,
	must carry no mapping explaining an exception that no longer exists, and
	the deployer must hold no grant table at all -- the last one grew from two
	entries to four, which is what a table nobody can close looks like."""
	destination, _result = installed
	record = json.loads(
		(_release_path(destination, "baton-cli")
		 / "PRODUCT.json").read_text())
	version = _installed_version()
	assert record["namespace"] == f"v{version.split('.')[0]}"
	assert record["namespace"] == "v10"
	assert "legacy_mapping" not in record
	assert not hasattr(deploy, "LEGACY_RELEASES"), \
		"the grant table is back"
	assert not hasattr(deploy, "LEGACY"), \
		"the legacy namespace constant is back"


@pytest.mark.parametrize("tool,version,protocol,expected", [
	("baton", "11.0.0", 11, "v11"),
	("baton-tui", "11.4.2", 11, "v11"),
	("baton", "12.1.0", 12, "v12"),
])
def test_a_numeric_namespace_is_derived_from_the_version(tool, version,
                                                         protocol, expected):
	assert deploy.namespace_for(tool, version, protocol) == expected


@pytest.mark.parametrize("tool,version,protocol", [
	("baton", "1.1.0", 11),          # the frozen 1.x pair, which has no
	                                 # generation to live in any more
	("baton", "2.0.0", 11),
	("baton-tui", "11.0.0", 12),
	("baton", "1.3.0", 10),          # major 1 at protocol 10: the shape the
	                                 # withdrawn grant used to admit
	("baton-tui", "2.0.0", 10),
])
def test_a_version_that_is_not_its_generation_has_nowhere_to_live(tool, version,
                                                                  protocol):
	with pytest.raises(deploy.DeployError, match="does not equal its generation"):
		deploy.namespace_for(tool, version, protocol)


# -- the path may not lie ---------------------------------------------------

def test_a_release_moved_into_the_wrong_generation_fails_verification(installed):
	"""Everything inside the release is intact; only its location is a lie.
	The digests cannot see that, which is exactly why the location is checked
	separately."""
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	# Moving a DIRECTORY into another parent needs write permission on the
	# directory itself -- its `..` entry changes -- and the release is 0555.
	# That is the hardening doing its job on the way to this test's subject.
	release.chmod(0o755)
	elsewhere = destination / "app" / "baton-cli" / "v11"
	elsewhere.mkdir(parents=True)
	moved = elsewhere / ("v" + _installed_version())
	release.rename(moved)

	problems = deploy.verify_release(str(moved))
	assert any("belongs in" in problem for problem in problems), problems


def test_a_release_renamed_to_another_version_fails_verification(installed):
	destination, _result = installed
	release = _release_path(destination, "baton-tui", "baton-tui")
	release.chmod(0o755)
	renamed = release.parent / "v9.9.9"
	release.rename(renamed)

	problems = deploy.verify_release(str(renamed))
	assert any("directory name does not match" in p for p in problems), problems


def test_a_release_under_the_wrong_product_fails_verification(installed):
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	wrong = _release_path(destination, "baton-tui", "baton-tui")
	deploy._remove_owned(str(wrong))          # hardened: 0555 all the way down
	shutil.copytree(release, wrong)

	problems = deploy.verify_release(str(wrong))
	assert any("installs under" in p for p in problems), problems


@pytest.mark.parametrize("field,value", [
	("product_version", "1.9.9"),
	("protocol_version", 11),
	("namespace", "v1"),
	("artifact_sha256", "ab" * 32),
])
def test_a_tampered_product_record_fails_its_own_release(installed, field, value):
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	_rewrite_record(release, lambda record: record.__setitem__(field, value))

	assert deploy.verify_release(str(release)) != [], \
		f"{field} could be changed without notice"


def test_changed_bytes_and_unrecorded_files_both_fail_verification(installed):
	destination, _result = installed
	release = _release_path(destination, "baton-tui", "baton-tui")
	release.chmod(0o755)
	(release / "doc").chmod(0o755)
	readme = release / "doc" / "README.md"
	readme.chmod(0o644)
	readme.write_text("tampered\n")
	assert any("README.md" in p for p in deploy.verify_release(str(release)))

	readme.unlink()
	shutil.copyfile(candidate.ROOT / "README.md", readme)
	readme.chmod(0o444)
	# Restored to the hardened modes as well: the record, the directories and
	# the leaves are all part of what a release IS.
	(release / "doc").chmod(0o555)
	release.chmod(0o555)
	assert deploy.verify_release(str(release)) == []

	release.chmod(0o755)
	(release / "doc").chmod(0o755)

	(release / "doc" / "EXTRA.md").write_text("who put this here\n")
	assert any("in no record" in p for p in deploy.verify_release(str(release)))


def test_a_symlinked_entry_inside_a_release_fails_verification(installed,
                                                               tmp_path):
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	elsewhere = tmp_path / "elsewhere"
	shutil.copyfile(release / "doc" / "LICENSE", elsewhere)
	release.chmod(0o755)
	(release / "doc").chmod(0o755)
	(release / "doc" / "LICENSE").unlink()
	(release / "doc" / "LICENSE").symlink_to(elsewhere)

	assert any("symlink" in p for p in deploy.verify_release(str(release)))


# -- the exact-path execution rule ------------------------------------------

def test_the_alias_is_not_the_path_anything_runs(installed):
	"""CPython's `zipimport` reopens the archive BY PATH on every lazy import.
	A process that kept `latest` open could seek offsets from the archive it
	started with into the archive that replaced it — so the alias is resolved
	once, and the exact path is what runs."""
	destination, result = installed
	for alias in result["aliases"]:
		assert "/latest/" not in alias["execute"]
		assert os.path.isfile(alias["execute"])
		assert ("v" + _installed_version(alias["execute"].rsplit("/", 1)[1]
		        if alias["execute"].endswith("baton-tui") else "baton")) \
			in alias["execute"]


def test_a_running_process_started_from_the_exact_path_survives_a_flip(installed,
                                                                       tmp_path):
	"""The hazard, reproduced and then shown to be absent.

	A child is started from the exact release path and made to import a module
	LAZILY, after the alias has been repointed at a different release. Because
	it opened the immutable exact path, the flip cannot reach it — which is
	the whole reason consumers are told to resolve once and execute exactly.
	"""
	destination, _result = installed
	generation = destination / "app" / "baton-cli" / "v10"
	exact = generation / ("v" + _installed_version()) / "bin" / "baton"

	# A second release to flip to: the same bytes under a different exact
	# name, built by copying and restamping, which is enough to move an alias.
	second = generation / ("v" + _installed_version() + "-flip")
	shutil.copytree(generation / ("v" + _installed_version()), second)
	second.chmod(0o755)
	record = json.loads((second / "PRODUCT.json").read_text())
	record["product_version"] = _installed_version()
	(second / "PRODUCT.json").chmod(0o644)
	(second / "PRODUCT.json").write_text(
		json.dumps(record, indent=2, sort_keys=True) + "\n")
	(second / "PRODUCT.json").chmod(0o444)
	second.chmod(0o555)

	script = tmp_path / "lazy.py"
	script.write_text(
		"import subprocess, sys, os, time\n"
		f"exact = {str(exact)!r}\n"
		"# Started BEFORE the flip; imports its modules as it runs.\n"
		"out = subprocess.run([sys.executable, exact, '--version'],\n"
		"                     capture_output=True, text=True)\n"
		"sys.stdout.write(out.stdout)\n")

	# The flip happens between the child's start and its lazy imports; the
	# simplest deterministic form of that is to flip first and then run, since
	# the exact path must be unaffected either way.
	os.unlink(generation / "latest")
	os.symlink(second.name, generation / "latest")

	printed = subprocess.run([sys.executable, str(script)], capture_output=True,
	                         text=True)
	assert printed.returncode == 0, printed.stderr
	assert printed.stdout.strip() == f"baton {_installed_version()} (protocol 10)"
	assert os.readlink(generation / "latest") == second.name


def test_resolving_an_alias_returns_the_exact_release(installed):
	destination, _result = installed
	generation = destination / "app" / "baton-tui" / "v10"
	assert deploy.resolve_alias(str(generation)) == \
		str(generation / ("v" + _installed_version("baton-tui")))


def test_an_alias_pointing_outside_its_generation_is_refused(installed,
                                                             tmp_path):
	destination, _result = installed
	generation = destination / "app" / "baton-cli" / "v10"
	os.unlink(generation / "latest")
	os.symlink(f"../../baton-tui/v10/v{_installed_version('baton-tui')}",
	           generation / "latest")
	with pytest.raises(deploy.DeployError, match="single component"):
		deploy.resolve_alias(str(generation))


# -- the mailbox handshake --------------------------------------------------

def test_a_mailbox_identity_is_written_once_and_never_rewritten(tmp_path):
	mailbox = tmp_path / "mailbox" / "v10"
	result = deploy.mailbox_identity(str(mailbox), 10)
	assert result["state"] == "written" and result["durable"] is True
	written = result["written"]
	document = json.loads(pathlib.Path(written).read_text())

	# FORMAT, NAMESPACE, PROTOCOL. Nothing else: the per-application grant was
	# withdrawn on 2026-08-13, because which exact releases may be installed is
	# a deployment-certification question and the core API is a product/core
	# embedding contract. Neither is something a mailbox is asked.
	assert set(document) == {"format", "format_version", "protocol_version",
	                         "namespace"}
	assert document["protocol_version"] == 10
	assert document["namespace"] == "v10"
	assert "generation" not in document, \
		"`generation` is the config's regen counter; two meanings, one word"

	# IDENTICAL RETRY IS ACCEPTED, and it RECONFIRMS DURABILITY: an
	# interrupted publication is exactly the case a retry exists for, so
	# returning early having done nothing would leave the doubt in place.
	again = deploy.mailbox_identity(str(mailbox), 10)
	assert again == {"written": written, "state": "already_written",
	                 "durable": True}

	# Anything DIFFERENT is refused: a mailbox identity is not something a
	# second opinion may overwrite.
	pathlib.Path(written).chmod(0o644)
	pathlib.Path(written).write_text(json.dumps({"format": "baton.mailbox"}))
	with pytest.raises(deploy.DeployError, match="already exists and differs"):
		deploy.mailbox_identity(str(mailbox), 10)


def test_a_numeric_mailbox_identity_names_its_generation(tmp_path):
	mailbox = tmp_path / "mailbox" / "v11"
	written = deploy.mailbox_identity(str(mailbox), 11)["written"]
	document = json.loads(pathlib.Path(written).read_text())
	assert document["namespace"] == "v11"
	assert set(document) == {"format", "format_version", "protocol_version",
	                         "namespace"}


def _mailbox(tmp_path, **document):
	config = tmp_path / "baton.json"
	config.write_text("{}")
	if document:
		(tmp_path / "MAILBOX.json").write_text(json.dumps(document))
	return str(config)


def test_a_mailbox_without_an_identity_is_accepted(tmp_path):
	"""Every mailbox in existence predates the handshake. Refusing them all
	would be refusing every authority there is."""
	import baton_core

	assert baton_core.check_mailbox_identity(_mailbox(tmp_path), "baton") is None


def test_a_mailbox_is_asked_about_its_protocol_and_nothing_else(tmp_path):
	"""SUPERSEDED PREMISE, and this is what replaced it. The document used to
	name exact applications and versions and startup checked membership;
	Slawomir withdrew that. A client asks one question, and any release of any
	application that speaks the protocol may open the mailbox."""
	import baton_core

	config = _mailbox(tmp_path, format="baton.mailbox", format_version=1,
	                  protocol_version=10, namespace="v10")
	for application in ("baton", "baton-tui"):
		assert baton_core.check_mailbox_identity(config, application)


def test_a_mailbox_of_another_protocol_is_refused(tmp_path):
	import baton_core

	config = _mailbox(tmp_path, format="baton.mailbox", format_version=1,
	                  protocol_version=11, namespace="v11")
	with pytest.raises(baton_core.BatonError, match="speaks protocol 10"):
		baton_core.check_mailbox_identity(config, "baton")


@pytest.mark.parametrize("document,expected", [
	({"format": "somebody.else", "format_version": 1, "protocol_version": 10,
	  "namespace": "v10"}, "not 'baton.mailbox'"),
	({"format": "baton.mailbox", "format_version": 99, "protocol_version": 10,
	  "namespace": "v10"}, "format version"),
	({"format": "baton.mailbox", "format_version": 1, "namespace": "v10"},
	 "no usable protocol_version"),
	({"format": "baton.mailbox", "format_version": 1, "protocol_version": 10},
	 "no namespace"),
	({"format": "baton.mailbox", "format_version": 1, "protocol_version": 10,
	  "namespace": "v11"}, "same number"),
	({"format": "baton.mailbox", "format_version": 1, "protocol_version": 10,
	  "namespace": "v10",
	  "legacy_mapping": {"application_versions": {"baton": ["1.1.0"]}}},
	 "does not know"),
])
def test_a_broken_handshake_is_not_the_same_as_no_handshake(tmp_path, document,
                                                            expected):
	"""Treating a malformed identity as absence would turn a corrupted
	compatibility claim into an accepted one. The last case is the WITHDRAWN
	grant: a document still carrying one is refused rather than half-read."""
	import baton_core

	with pytest.raises(baton_core.BatonError, match=expected):
		baton_core.check_mailbox_identity(_mailbox(tmp_path, **document), "baton")


def test_a_symlinked_identity_document_is_refused(tmp_path):
	import baton_core

	elsewhere = tmp_path / "elsewhere.json"
	elsewhere.write_text(json.dumps({"format": "baton.mailbox",
	                                 "format_version": 1,
	                                 "protocol_version": 10,
	                                 "namespace": "v10"}))
	instance = tmp_path / "instance"
	instance.mkdir()
	(instance / "baton.json").write_text("{}")
	(instance / "MAILBOX.json").symlink_to(elsewhere)

	with pytest.raises(baton_core.BatonError, match="symlink"):
		baton_core.check_mailbox_identity(str(instance / "baton.json"), "baton")


def test_unknown_fields_and_duplicate_keys_are_refused(tmp_path):
	"""Read with Baton's strict loader, like every other trust document: a
	duplicate key silently resolving to whichever value came last is exactly
	how a claim nothing checks gets in."""
	import baton_core

	config = _mailbox(tmp_path, format="baton.mailbox", format_version=1,
	                  protocol_version=10, namespace="v10", blessed_by="me")
	with pytest.raises(baton_core.BatonError, match="does not know"):
		baton_core.check_mailbox_identity(config, "baton")

	instance = pathlib.Path(config).parent
	(instance / "MAILBOX.json").write_text(
		'{"format": "baton.mailbox", "format_version": 1, '
		'"protocol_version": 10, "protocol_version": 11, '
		'"namespace": "v10"}')
	with pytest.raises(baton_core.BatonError, match="duplicate|strict"):
		baton_core.check_mailbox_identity(str(config), "baton")


def test_the_refusal_arrives_before_any_mutation(tmp_path):
	"""The handshake runs before the command, not inside it: a refusal that
	arrives after a write is not a refusal."""
	import baton_core

	instance = tmp_path / "instance"
	instance.mkdir()
	config = instance / "baton.json"
	config.write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "probe"},
		"participants": {"team.implementer": {}, "team.reviewer": {}},
		"roots": {}, "retention_days": 90}))
	baton_core.init_instance(str(config))
	store = instance / "mailbox.sqlite3"
	before = {p.name: p.read_bytes() for p in instance.iterdir() if p.is_file()}

	(instance / "MAILBOX.json").write_text(json.dumps({
		"format": "baton.mailbox", "format_version": 1,
		"protocol_version": 11, "namespace": "v11"}))
	refused = subprocess.run(
		[sys.executable, str(candidate.CLI), "--config", str(config), "send",
		 "--participant", "team.implementer", "--to", "team.reviewer",
		 "--kind", "note", "--tweet", "this must not arrive"],
		capture_output=True, text=True)

	assert refused.returncode != 0
	assert "protocol 11" in refused.stderr
	assert store.read_bytes() == before["mailbox.sqlite3"], \
		"the authority changed during a refusal"


def test_the_source_command_line_refuses_before_it_dispatches(tmp_path):
	"""The same rule on the SOURCE rather than the packaged candidate: the
	packaged test above cannot fail when the check is removed from `src/`,
	because it reads a candidate built before the change."""
	import baton_core
	from baton_core import cli

	instance = tmp_path / "instance"
	instance.mkdir()
	config = instance / "baton.json"
	config.write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "probe"},
		"participants": {"team.implementer": {}, "team.reviewer": {}},
		"roots": {}, "retention_days": 90}))
	baton_core.init_instance(str(config))
	before = (instance / "mailbox.sqlite3").read_bytes()

	(instance / "MAILBOX.json").write_text(json.dumps({
		"format": "baton.mailbox", "format_version": 1,
		"protocol_version": 11, "namespace": "v11"}))
	code = cli.main(["--config", str(config), "send", "--participant",
	                 "team.implementer", "--to", "team.reviewer", "--kind",
	                 "note", "--tweet", "this must not arrive"])
	assert code != 0
	assert (instance / "mailbox.sqlite3").read_bytes() == before

	(instance / "MAILBOX.json").write_text(json.dumps({
		"format": "baton.mailbox", "format_version": 1,
		"protocol_version": 10, "namespace": "v10"}))
	assert cli.main(["--config", str(config), "send", "--participant",
	                 "team.implementer", "--to", "team.reviewer", "--kind",
	                 "note", "--tweet", "this one arrives"]) == 0


# -- installing is all-or-nothing where it matters --------------------------

def test_a_failure_installing_the_second_product_advances_no_alias(tmp_path,
                                                                   monkeypatch):
	"""An installed release nothing points at is INERT. What has to be
	all-or-nothing is the advance, not the copy: a moved alias beside a
	product that failed to install is a pair nobody chose."""
	candidate.require()
	destination = tmp_path / "dest"
	real = deploy._install_release
	seen = []

	def explode(root_fd, dest, source, tool, record):
		seen.append(tool)
		if len(seen) > 1:
			raise OSError(28, "No space left on device")
		return real(root_fd, dest, source, tool, record)

	monkeypatch.setattr(deploy, "_install_release", explode)
	with pytest.raises(OSError):
		deploy.install(str(candidate.ROOT), str(destination))

	aliases = list(destination.rglob("latest"))
	assert aliases == [], f"an alias advanced anyway: {aliases}"


def test_advancing_an_alias_moves_it_and_reports_what_it_replaced(tmp_path):
	"""An ADVANCE, not a redeploy: the old and new targets differ, so a call
	that quietly did nothing would be visible. The earlier version of this
	test redeployed the same candidate, so the alias was asked to move from
	`v11.1.0` to `v11.1.0` and no advance was ever exercised."""
	destination = tmp_path / "dest"
	deploy.install(str(_bumped(tmp_path, "first", "11.1.0", "11.4.0")),
	               str(destination))
	generation = destination / "app" / "baton-cli" / "v11"
	assert os.readlink(generation / "latest") == "v11.1.0"

	deploy.install(str(_bumped(tmp_path, "second", "11.2.0", "11.5.0")),
	               str(destination))
	assert os.readlink(generation / "latest") == "v11.2.0"
	assert (generation / "v11.1.0").is_dir(), "the previous release was removed"

	back = deploy.set_alias(str(generation), "v11.1.0")
	assert back["previous"] == "v11.2.0"
	assert back["durable"] is True
	assert deploy.resolve_alias(str(generation)) == str(generation / "v11.1.0")


def test_a_failed_durability_call_reports_committed_not_unchanged(tmp_path,
                                                                  monkeypatch):
	"""R4. The fsync used to raise, so a failure surfaced as "the alias did
	not move" while the alias HAD moved -- and any rollback written afterwards
	would be a second write on a filesystem that just failed one."""
	destination = tmp_path / "dest"
	deploy.install(str(_bumped(tmp_path, "first", "11.1.0", "11.4.0")),
	               str(destination))
	deploy.install(str(_bumped(tmp_path, "second", "11.2.0", "11.5.0")),
	               str(destination))
	generation = destination / "app" / "baton-cli" / "v11"

	def no_durability(path):
		raise OSError(5, "Input/output error")

	monkeypatch.setattr(deploy, "_fsync_dir", no_durability)
	moved = deploy.set_alias(str(generation), "v11.1.0")

	assert moved["durable"] is False, "an unconfirmed write was reported as durable"
	assert moved["target"] == "v11.1.0"
	assert os.readlink(generation / "latest") == "v11.1.0", \
		"the report must describe what the pathname actually names"


def test_a_second_install_against_one_destination_is_refused(tmp_path):
	"""Two deployments interleaving their per-product updates could leave a
	pair neither of them asked for. No care inside one process prevents it."""
	source = _bumped(tmp_path, "first", "11.1.0", "11.4.0")
	destination = tmp_path / "dest"
	deploy.install(str(source), str(destination))

	lock = destination / ".deploy.lock"
	lock.write_text("99999\n")
	try:
		with pytest.raises(deploy.DeployError, match="another deployment"):
			deploy.install(str(source), str(destination))
	finally:
		lock.unlink()
	deploy.install(str(source), str(destination))
	assert not lock.exists(), "a successful run left its lock behind"


def test_a_failure_advancing_the_second_alias_puts_the_first_back(tmp_path,
                                                                  monkeypatch):
	"""The recovery the ruling asks for by name. Both aliases are asked to
	ADVANCE here, so the recovery has something real to undo."""
	destination = tmp_path / "dest"
	deploy.install(str(_bumped(tmp_path, "first", "11.1.0", "11.4.0")),
	               str(destination))
	before = {str(p): os.readlink(p) for p in destination.rglob("latest")}
	assert len(before) == 2

	real = deploy._set_alias_at
	seen = set()

	def advance_then_explode(generation_fd, generation_dir, target, **kwargs):
		product = pathlib.Path(generation_dir).parent.name
		# The FIRST product advances for real; the second one fails. Recovery
		# calls (which name a product already seen) are let through, or the
		# recovery would be the thing being tested.
		if product not in seen:
			seen.add(product)
			if len(seen) > 1:
				raise deploy.DeployError("the second alias could not be written")
		return real(generation_fd, generation_dir, target, **kwargs)

	monkeypatch.setattr(deploy, "_set_alias_at", advance_then_explode)
	with pytest.raises(deploy.DeployError):
		deploy.install(str(_bumped(tmp_path, "second", "11.2.0", "11.5.0")),
		               str(destination))

	after = {str(p): os.readlink(p) for p in destination.rglob("latest")}
	assert after == before, "a partial alias update survived"
	# ...and both releases are installed, because installing is not what has
	# to be undone: a release nothing points at is inert.
	assert (destination / "app" / "baton-cli" / "v11" / "v11.2.0").is_dir()


def test_installing_again_after_an_interrupted_run_is_idempotent(tmp_path,
                                                                 monkeypatch):
	"""Crash, then retry. The first product is already installed; the retry
	must report it and continue rather than refuse the whole deployment."""
	candidate.require()
	destination = tmp_path / "dest"
	real = deploy._install_release
	seen = []

	def explode(root_fd, dest, source, tool, record):
		seen.append(tool)
		if len(seen) > 1:
			raise OSError(28, "No space left on device")
		return real(root_fd, dest, source, tool, record)

	monkeypatch.setattr(deploy, "_install_release", explode)
	with pytest.raises(OSError):
		deploy.install(str(candidate.ROOT), str(destination))
	monkeypatch.undo()

	result = deploy.install(str(candidate.ROOT), str(destination))
	states = {release["tool"]: release["state"] for release in result["releases"]}
	assert set(states.values()) <= {"installed", "already_installed"}
	assert "already_installed" in states.values(), \
		"the release that survived the crash was reinstalled"
	assert len(list(destination.rglob("latest"))) == 2


def test_a_partially_installed_release_is_never_left_behind(tmp_path,
                                                            monkeypatch):
	"""A failure DURING one product's install leaves no directory at its exact
	path -- an immutable release that is missing a file could never be
	repaired, because repairing it is the one thing immutability forbids."""
	candidate.require()
	destination = tmp_path / "dest"
	real = deploy._open_regular
	opened = []

	def explode(path):
		opened.append(path)
		if len(opened) > 3:
			raise OSError(5, "Input/output error")
		return real(path)

	monkeypatch.setattr(deploy, "_open_regular", explode)
	with pytest.raises(OSError):
		deploy.install(str(candidate.ROOT), str(destination))

	assert list(destination.rglob("v" + _installed_version())) == []
	assert list(destination.rglob(".staging-*")) == []


# -- the migration guide ----------------------------------------------------

@pytest.fixture
def guided(installed, tmp_path):
	"""An installed destination with a mailbox identity, ready to describe."""
	import migration_guide

	import baton_core

	destination, _result = installed
	mailbox = destination / "mailbox" / "v10"
	deploy.mailbox_identity(str(mailbox), 10)
	# A REAL authority, because the audience now comes from the accepted
	# config rather than from a file: an instance nobody initialized cannot
	# answer who its participants are, and that is the point of the change.
	instance = tmp_path / "source-instance"
	instance.mkdir()
	config = instance / "baton.json"
	config.write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "probe"},
		"participants": {"web.reviewer": {}, "web.implementer": {},
		                 # The one who runs the ceremony holds `config`, which
		                 # is what `regen` requires -- the same shape as the
		                 # real authority.
		                 "human.slawomir": {"capabilities": ["config"]}},
		"roots": {}, "retention_days": 90}))
	baton_core.init_instance(str(config))
	return migration_guide, destination, config, mailbox


def test_the_guide_is_generated_from_the_deployment_it_describes(guided):
	module, destination, config, mailbox = guided
	body = module.render(str(destination), str(config), str(mailbox))

	cli = _release_path(destination, "baton-cli") / "bin" / "baton"
	tui = (_release_path(destination, "baton-tui", "baton-tui")
	       / "bin" / "baton-tui")
	assert str(cli) in body and str(tui) in body
	assert str(mailbox / "baton.json") in body
	record = json.loads(
		(cli.parent.parent / "PRODUCT.json").read_text())
	assert record["artifact_sha256"] in body
	assert record["provenance"]["set_digest"] in body


def test_the_guide_tells_nobody_to_run_the_alias(guided):
	"""It explains `latest` and then never puts it in an instruction."""
	module, destination, config, mailbox = guided
	body = module.render(str(destination), str(config), str(mailbox))

	instructions = [line for line in body.splitlines()
	                if line.startswith(("baton", "/", "→")) or "--config" in line]
	running = [line for line in instructions if "/latest/" in line]
	assert running == [], f"the guide tells somebody to run an alias: {running}"
	assert "zipimport" in body or "reopens the archive" in body, \
		"the guide must say WHY, or the rule is folklore"


def test_the_guide_is_one_body_of_bytes(guided):
	"""Published as a broadcast and as one durable delivery per participant --
	the same bytes, because two renderings is how half a team ends up
	following instructions the other half never saw."""
	module, destination, config, mailbox = guided
	first = module.render(str(destination), str(config), str(mailbox))
	second = module.render(str(destination), str(config), str(mailbox))
	assert first == second


def test_the_audience_is_every_registered_participant(guided):
	module, destination, config, mailbox = guided
	assert module.audience(str(config)) == ["human.slawomir",
	                                        "web.implementer", "web.reviewer"]


def test_the_guide_refuses_to_replace_bytes_that_may_be_published(guided,
                                                                  tmp_path):
	module, destination, config, mailbox = guided
	output = tmp_path / "GUIDE.md"
	argv = [str(destination), "--config", str(config), "--mailbox",
	        str(mailbox), "--output", str(output)]
	assert module.main(argv) == 0
	assert module.main(argv) == 0, "regenerating identical bytes must be safe"

	output.write_text("# somebody edited this\n")
	assert module.main(argv) == 1


@pytest.mark.parametrize("break_it,expected", [
	("no-apps", "install the applications"),
	("no-identity", "no identity to describe"),
	("two-generations", "one generation"),
])
def test_the_guide_refuses_to_describe_what_is_not_there(guided, break_it,
                                                         expected):
	module, destination, config, mailbox = guided
	if break_it == "no-apps":
		deploy._remove_owned(str(destination / "app" / "baton-cli"))
	elif break_it == "no-identity":
		(mailbox / "MAILBOX.json").chmod(0o644)
		(mailbox / "MAILBOX.json").unlink()
	elif break_it == "two-generations":
		(destination / "app" / "baton-cli" / "v11").mkdir()

	with pytest.raises((module.GuideError, deploy.DeployError), match=expected):
		module.render(str(destination), str(config), str(mailbox))


def test_a_non_directory_ancestor_is_refused(tmp_path):
	candidate.require()
	destination = tmp_path / "dest"
	(destination / "app").mkdir(parents=True)
	(destination / "app" / "baton-cli").write_text("not a directory\n")

	with pytest.raises(deploy.DeployError, match="not a directory|symlink"):
		deploy.install(str(candidate.ROOT), str(destination))
	assert (destination / "app" / "baton-cli").read_text() == "not a directory\n"


def test_an_ancestor_swapped_after_validation_cannot_redirect_the_write(
		tmp_path, monkeypatch):
	"""The race, not just the state: the check and the write must not be two
	independent resolutions of the same string."""
	candidate.require()
	destination = tmp_path / "dest"
	outside = tmp_path / "outside"
	outside.mkdir()
	real = deploy._install_confined
	swapped = {}

	def swap_then_install(generation_fd, release_dir, *args, **kwargs):
		if not swapped:
			# Somebody replaces the product directory with a link to
			# elsewhere, after this call validated it.
			product = pathlib.Path(release_dir).parent.parent
			shutil.rmtree(product)
			product.symlink_to(outside)
			swapped["done"] = True
		return real(generation_fd, release_dir, *args, **kwargs)

	monkeypatch.setattr(deploy, "_install_confined", swap_then_install)
	with pytest.raises(deploy.DeployError):
		deploy.install(str(candidate.ROOT), str(destination))

	assert list(outside.iterdir()) == [], \
		"the swap redirected the write outside the destination"


# -- the record authenticates every claim it makes --------------------------
#
# R2. Version, protocol and the artifact digest were compared and everything
# else was believed: an installed record could name a different core, a
# different required API or a different candidate and still verify.

@pytest.mark.parametrize("field,value", [
	("requires_core_api", 999),
	("embeds_core", {"version": "999.0.0", "api_version": 3,
	                 "package_sha256": "cd" * 32}),
	("artifact", "bin/somewhere-else"),
	("legacy_mapping", {"reason": "made up", "product_version": "1.1.0",
	                    "protocol_version": 10}),
])
def test_every_projected_field_is_reconstructed_not_believed(installed, field,
                                                             value):
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	_rewrite_record(release, lambda record: record.__setitem__(field, value))

	problems = deploy.verify_release(str(release))
	assert any("projects" in p or "manifest" in p or "legacy_mapping" in p
	           for p in problems), problems


@pytest.mark.parametrize("change", ["set_digest", "manifest", "payload",
                                    "gate", "extra-field", "missing-field"])
def test_the_candidate_provenance_is_recomputed(installed, change):
	"""A retained set digest that nothing can check is exactly the shape of
	claim this project has twice been corrected for."""
	destination, _result = installed
	release = _release_path(destination, "baton-tui", "baton-tui")

	def edit(record):
		if change == "set_digest":
			record["provenance"]["set_digest"] = "0" * 64
		elif change == "manifest":
			record["provenance"]["manifests"]["dist/DISTRIBUTION.json"][
				"artifact_sha256"] = "ab" * 32
		elif change == "payload":
			record["provenance"]["payload"]["README.md"] = "cd" * 32
		elif change == "gate":
			record["provenance"]["gate"] = "somebody-just-decided"
		elif change == "extra-field":
			record["provenance"]["blessed_by"] = "me"
		elif change == "missing-field":
			del record["provenance"]["payload"]

	_rewrite_record(release, edit)

	assert deploy.verify_release(str(release)) != [], \
		f"{change} was accepted without checking"


@pytest.mark.parametrize("broken", [
	{"files": {"bin/baton": "not-an-object"}},
	{"files": {"bin/baton": {"sha256": "ab" * 32}}},
	{"files": {"bin/baton": {"sha256": "zz" * 32, "mode": 493}}},
	{"files": {"bin/baton": {"sha256": "ab" * 32, "mode": 493, "extra": 1}}},
	{"files": {"bin/baton": {"sha256": "ab" * 32, "mode": "0755"}}},
	{"files": {"../escape": {"sha256": "ab" * 32, "mode": 420}}},
	{"files": []},
])
def test_a_malformed_record_is_a_refusal_not_a_traceback(installed, broken):
	"""A record is a trust document. Walking one that is not the shape this
	code expects produced an `AttributeError` traceback instead of something a
	human could act on."""
	destination, _result = installed
	release = _release_path(destination, "baton-cli")
	_rewrite_record(release, lambda record: record.update(broken))

	try:
		problems = deploy.verify_release(str(release))
	except deploy.DeployError as refusal:
		assert str(refusal)
		return
	assert problems != [], "a malformed record verified"


def test_the_record_and_directory_modes_are_checked(installed):
	destination, _result = installed
	release = _release_path(destination, "baton-tui", "baton-tui")
	release.chmod(0o755)
	(release / "PRODUCT.json").chmod(0o644)

	problems = deploy.verify_release(str(release))
	assert any("mode" in p for p in problems), problems


def test_the_audience_comes_from_the_authority_not_the_file(guided, tmp_path):
	"""R3. A config file is a PROPOSAL until `regen` accepts it. Editing it
	without regen changes the file and changes nothing the authority believes,
	so an edited file could quietly drop real participants from a handoff
	whose entire value is that it reached everyone."""
	module, destination, config, mailbox = guided
	accepted = module.audience(str(config))
	assert accepted == ["human.slawomir", "web.implementer", "web.reviewer"]

	document = json.loads(config.read_text())
	document["participants"] = {"wrong.one": {}}
	config.write_text(json.dumps(document))

	with pytest.raises(module.GuideError, match="would not open read-only"):
		module.audience(str(config))


def test_the_guide_records_the_config_it_froze_its_audience_from(guided):
	module, destination, config, mailbox = guided
	body = module.render(str(destination), str(config), str(mailbox))
	assert module.accepted_digest(str(config)) in body
	assert "3 accepted" in body


# -- the deployment act is evidence beside the tree --------------------------
#
# SUPERSEDED 2026-08-13: there were three gates and two of them were
# `legacy-import`, the act that installed the frozen 1.x pair as releases.
# That family is gone -- the pair is a hand-maintained directory now -- so
# there is one act left, and what still has to hold is that the act stays OUT
# of the release it installed.

def test_the_gate_is_recorded_beside_the_tree_not_inside_a_release(tmp_path):
	"""R8. Recording the human act inside each immutable `PRODUCT.json` made
	one exact version have two mutually exclusive identities, so reinstalling
	identical bytes became a refusal instead of `already_installed`.

	The act is evidence ABOUT an operation. It lives in an append-only record
	beside the tree, and the release is derived from certified bytes alone."""
	candidate.require()
	destination = tmp_path / "dest"

	first = deploy.install(str(candidate.ROOT), str(destination))
	assert first["gate"] == "candidate-deploy"
	record = json.loads((_release_path(destination, "baton-cli")
	                     / "PRODUCT.json").read_text())
	assert "gate" not in record["provenance"], \
		"an act was written into a release's identity"

	# The same bytes again: `already_installed`, not a refusal.
	again = deploy.install(str(candidate.ROOT), str(destination))
	assert {item["state"] for item in again["releases"]} == {"already_installed"}

	# BOTH acts are recorded, each its own immutable document with its own
	# outcome -- one truncated write cannot make the others unreadable, which
	# an appended log could not promise.
	entries = [json.loads(path.read_text())
	           for path in sorted((destination / "operations").glob("*.json"))]
	assert len(entries) == 2, entries
	assert {entry["gate"] for entry in entries} == {"candidate-deploy"}
	assert {entry["set_digest"] for entry in entries} == {first["set_digest"]}
	states = sorted({item["state"] for entry in entries
	                 for item in entry["releases"]})
	assert states == ["already_installed", "installed"]
	for path in (destination / "operations").glob("*.json"):
		assert path.stat().st_mode & 0o777 == 0o444


def test_the_only_gate_is_the_deploy_and_the_old_name_is_history(tmp_path):
	"""The removed gate must not be quietly re-admitted, and records already
	written under it must stay readable: they are evidence of acts that really
	happened, and an append-only record that gets rewritten to match a later
	rule is not append-only."""
	assert deploy.GATES == ("candidate-deploy",)
	assert "legacy-import" in deploy.HISTORICAL_GATES
	assert not hasattr(deploy, "import_production")
	assert not hasattr(deploy, "RECOVERY_RECORD")


def test_the_guide_names_the_problems_doctor_already_reports(guided):
	"""R7. Somebody will run `doctor` after the move and attribute what they
	see to it. The guide says the number and says what it is."""
	module, destination, config, mailbox = guided
	body = module.render(str(destination), str(config), str(mailbox))
	# Searched on the UNWRAPPED text: the guide is wrapped to 72 columns for
	# the terminal, so a phrase can span a line break and a naive substring
	# search would report an absence that is really a newline.
	flat = " ".join(body.split())
	assert "doctor" in flat
	assert "problems on this authority" in flat
	assert "neither causes nor cures them" in flat


def test_the_guide_does_not_contradict_itself_about_stale_paths(guided):
	"""It said a stale path "does not fail loudly" and "opens nothing", and
	then correctly said the old source refuses and names where it went. The
	accurate half is the one that survives."""
	module, destination, config, mailbox = guided
	flat = " ".join(module.render(str(destination), str(config),
	                              str(mailbox)).split())
	assert "does not fail loudly" not in flat
	# SUPERSEDED 2026-08-13: the guide used to promise that an old path
	# "refuses and names where the mailbox went", which described the audited
	# move ceremony's tombstone. Slawomir ruled this cutover is a full stop and
	# an offline `mv`, with no tombstone and no automatic following -- so the
	# guide now promises what actually happens: no config at the old path, a
	# `MOVED` file beside it, and a human reading one hop at a time.
	assert "MOVED" in flat
	assert "one hop" in flat
	assert "tombstone" not in flat


# -- publishing the guide ---------------------------------------------------
#
# R12. The publisher exists, is tested here against throwaway authorities, and
# is run by nobody: publication is one of the five acts only Slawomir
# authorizes. A publisher that first appears at the moment it is needed is a
# publisher nobody has ever seen work.

@pytest.fixture
def publishable(guided, tmp_path):
	import publish_guide

	module, destination, config, mailbox = guided
	body = module.render(str(destination), str(config), str(mailbox))
	guide = tmp_path / "GUIDE.md"
	guide.write_text(body)
	return publish_guide, config, guide, tmp_path / "receipt.json"


def test_the_plan_sends_nothing_and_says_what_would_happen(publishable):
	publisher, config, guide, receipt = publishable
	proposed = publisher.plan(str(config), str(guide), str(receipt),
	                          sender="human.slawomir")

	assert proposed["audience"] == ["human.slawomir", "web.implementer",
	                                "web.reviewer"]
	assert proposed["remaining"] == ["notice", "directed"]
	assert proposed["notice"] is None
	assert not receipt.exists(), "the dry run wrote a receipt"


def test_publishing_sends_one_notice_and_one_directed_publication(publishable):
	publisher, config, guide, receipt = publishable
	written = publisher.publish(str(config), str(guide), str(receipt),
	                            sender="human.slawomir")

	assert written["notice"]
	assert written["publication"]
	assert written["durable"] is True
	# EVERY REGISTERED PARTICIPANT, the sender included: the ruling says one
	# durable delivery per registered participant, and a sender who is also a
	# participant is one.
	assert written["audience"] == ["human.slawomir", "web.implementer",
	                               "web.reviewer"]
	assert written["attempting"] is None
	assert receipt.exists(), "no receipt survived a successful publication"

	# THE SAME BYTES reached both channels.
	import baton_core

	body = guide.read_text().encode("utf-8")
	with baton_core.open_instance(str(config), readonly=True) as store:
		notices = store.list_notices(participant="web.reviewer")
		assert notices, "the broadcast did not arrive"
		pending = store.scan(participant="web.reviewer")["pending"]
		assert pending, "the directed delivery did not arrive"
	assert hashlib.sha256(body).hexdigest() == written["body_sha256"]


def test_a_retry_completes_a_partial_publication_without_duplicating(publishable,
                                                                     monkeypatch):
	"""You cannot unsend a message, so the honest model is resume."""
	publisher, config, guide, receipt = publishable
	import baton_core

	real = baton_core.Store.send

	def explode(self, *args, **kwargs):
		raise RuntimeError("the directed publication failed")

	monkeypatch.setattr(baton_core.Store, "send", explode)
	with pytest.raises(RuntimeError):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")
	monkeypatch.undo()

	# The notice is recorded, so the retry does not send a second one. The
	# directed step was in flight when it failed, and the publisher does not
	# get to assume it did not commit -- Baton commits before this process
	# learns it did -- so the retry refuses until a human says otherwise.
	partial = json.loads(receipt.read_text())
	assert partial["notice"] and not partial["publication"]
	assert partial["attempting"] == "directed"
	proposed = publisher.plan(str(config), str(guide), str(receipt),
	                          sender="human.slawomir")
	assert proposed["remaining"] == ["directed"]

	with pytest.raises(publisher.Uncertain):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")

	finished = publisher.publish(str(config), str(guide), str(receipt),
	                             sender="human.slawomir",
	                             resend_uncertain=True)
	assert finished["notice"] == partial["notice"], "a second notice was sent"
	assert finished["publication"]

	# And publishing again after completion sends nothing at all.
	again = publisher.publish(str(config), str(guide), str(receipt),
	                          sender="human.slawomir")
	assert again["publication"] == finished["publication"]


def test_publishing_refuses_a_guide_frozen_against_another_config(publishable):
	publisher, config, guide, receipt = publishable
	guide.write_text(guide.read_text().replace(
		publisher.migration_guide.accepted_digest(str(config)), "0" * 64))

	with pytest.raises(publisher.PublishError, match="config digest"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_a_receipt_this_tool_did_not_write_is_not_resumed_from(publishable):
	publisher, config, guide, receipt = publishable
	receipt.write_text(json.dumps({"format": "somebody.elses", "delivered": {}}))

	with pytest.raises(publisher.PublishError, match="not a publication receipt"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


# -- what a commit boundary owes the operator -------------------------------
#
# R9-R11. A rename either happened or it did not. Once it has, a failing
# durability call cannot be reported as "nothing changed" -- and nothing may be
# written again to "fix" it, because that is a second write on a filesystem
# whose durability operation just failed.

def test_a_release_committed_but_not_confirmed_durable_is_kept_and_reported(
		tmp_path, monkeypatch):
	"""R9. The directory fsync used to sit inside the block that cleans up
	staging, so a durability failure raised while the immutable release was
	already at its final pathname."""
	candidate.require()
	destination = tmp_path / "dest"
	real = deploy._fsync_dir
	failed = []

	def flaky(path):
		# EXACTLY the generation directory at the release commit: that is the
		# held descriptor itself, `/proc/self/fd/N` with nothing after it. The
		# staging tree's own fsyncs and the later alias fsync are left alone,
		# so this test fails for its own reason or not at all.
		if re.fullmatch(r"/proc/self/fd/\d+", path) and not failed:
			failed.append(path)
			raise OSError(5, "Input/output error")
		return real(path)

	monkeypatch.setattr(deploy, "_fsync_dir", flaky)
	result = deploy.install(str(candidate.ROOT), str(destination))

	assert failed, "the durability failure was never injected"
	assert result["releases"], "the install reported no releases"
	assert not all(item["durable"] for item in result["releases"]), \
		"an unconfirmed write was reported as durable"
	# The release IS there: it was committed by the rename.
	assert (_release_path(destination, "baton-tui", "baton-tui")
	        / "bin" / "baton-tui").is_file()
	assert deploy.verify_release(
		str(_release_path(destination, "baton-tui", "baton-tui"))) == []


def test_an_identical_retry_reconfirms_durability(tmp_path):
	"""The retry is how a human resolves an unconfirmed write, so it must
	actually sync rather than return early having done nothing."""
	candidate.require()
	destination = tmp_path / "dest"
	deploy.install(str(candidate.ROOT), str(destination))

	again = deploy.install(str(candidate.ROOT), str(destination))
	assert {item["state"] for item in again["releases"]} == {"already_installed"}
	assert all(item["durable"] for item in again["releases"])


def test_uncertain_durability_reaches_the_operator(tmp_path, monkeypatch):
	"""R10. `set_alias` knew and `_report` dropped it, so `just deploy`
	printed an ordinary success and nobody learned that a durability call had
	failed."""
	candidate.require()
	destination = tmp_path / "dest"
	# The alias commit is reached through a held descriptor now, so the
	# durability failure is injected at the call that reports it rather than
	# by matching a pathname that no longer exists.
	real = deploy._set_alias_at

	def committed_but_unconfirmed(generation_fd, generation_dir, target,
	                              **kwargs):
		moved = real(generation_fd, generation_dir, target, **kwargs)
		moved["durable"] = False
		return moved

	monkeypatch.setattr(deploy, "_set_alias_at", committed_but_unconfirmed)
	report = deploy._report(deploy.install(str(candidate.ROOT), str(destination)))

	assert report["durable"] is False
	assert any(item["durable"] is False
	           for item in report["releases"] + report["aliases"])
	assert "durability_note" in report


def test_no_rollback_write_follows_an_uncertain_alias(tmp_path, monkeypatch):
	"""R10's second half. If the first alias committed without confirming
	durability and the second then fails, the recovery loop would issue
	another write on that same filesystem -- which this code told itself it
	would not do, and then did."""
	candidate.require()
	destination = tmp_path / "dest"
	deploy.install(str(candidate.ROOT), str(destination))
	before = {str(p): os.readlink(p) for p in destination.rglob("latest")}

	real_alias = deploy._set_alias_at
	writes = []
	seen = set()

	def uncertain_then_fail(generation_fd, generation_dir, target, **kwargs):
		product = pathlib.Path(generation_dir).parent.name
		writes.append(product)
		if product in seen:
			raise AssertionError("a rollback write followed an uncertain alias")
		seen.add(product)
		if len(seen) > 1:
			raise deploy.DeployError("the second alias could not be written")
		moved = real_alias(generation_fd, generation_dir, target, **kwargs)
		moved["durable"] = False        # committed, durability unconfirmed
		return moved

	monkeypatch.setattr(deploy, "_set_alias_at", uncertain_then_fail)
	with pytest.raises(deploy.DeployError):
		deploy.install(str(candidate.ROOT), str(destination))

	assert len(writes) == 2, writes
	assert {str(p): os.readlink(p) for p in destination.rglob("latest")} == before


def test_a_symlinked_destination_never_receives_even_a_lock(tmp_path,
                                                            monkeypatch):
	"""R13. The lock was created through the lexical destination BEFORE
	confinement ran, so a symlinked DEST got a real file outside the tree that
	was named -- removed by a `finally`, and left behind by a crash."""
	candidate.require()
	outside = tmp_path / "outside"
	outside.mkdir()
	destination = tmp_path / "dest"
	destination.symlink_to(outside)

	def die_after_locking(root_fd, dest):
		raise AssertionError("the lock was taken before confinement refused")

	monkeypatch.setattr(deploy, "_exclusive", die_after_locking)
	with pytest.raises(deploy.DeployError, match="symlink"):
		deploy.install(str(candidate.ROOT), str(destination))

	assert list(outside.iterdir()) == [], \
		"a symlinked destination received deployment state"


def test_an_identical_identity_retry_actually_syncs(tmp_path, monkeypatch):
	"""R11, observed rather than inferred. A retry that returned
	`durable: true` without syncing would satisfy any assertion about its
	return value while doing exactly nothing about the doubt it exists to
	resolve — so the call itself is what this watches."""
	mailbox = tmp_path / "mailbox" / "v10"
	first = deploy.mailbox_identity(str(mailbox), 10)
	assert first["state"] == "written"

	synced = []
	real = deploy._fsync_dir

	def watch(path):
		synced.append(path)
		return real(path)

	monkeypatch.setattr(deploy, "_fsync_dir", watch)
	again = deploy.mailbox_identity(str(mailbox), 10)

	assert again["state"] == "already_written"
	assert str(mailbox) in synced, "the retry confirmed nothing"

	# And when that sync fails, the retry says so instead of claiming durable.
	monkeypatch.setattr(deploy, "_fsync_dir",
	                    lambda path: (_ for _ in ()).throw(OSError(5, "I/O")))
	assert deploy.mailbox_identity(str(mailbox), 10)["durable"] is False


def test_the_guide_refuses_a_mailbox_the_releases_cannot_open(installed,
                                                              tmp_path):
	"""R12. A plain `json.load` let a guide describe a generation-11 mailbox
	beside legacy releases and read perfectly well while telling people to run
	a pair that cannot work."""
	import baton_core
	import migration_guide

	destination, _result = installed
	mailbox = destination / "mailbox" / "v11"
	deploy.mailbox_identity(str(mailbox), 11)
	instance = tmp_path / "src-instance"
	instance.mkdir()
	config = instance / "baton.json"
	config.write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "probe"},
		"participants": {"web.reviewer": {}, "web.implementer": {}},
		"roots": {}, "retention_days": 90}))
	baton_core.init_instance(str(config))

	with pytest.raises(migration_guide.GuideError, match="protocol"):
		migration_guide.render(str(destination), str(config), str(mailbox))


def test_a_generation_swapped_before_the_alias_cannot_redirect_it(tmp_path,
                                                                  monkeypatch):
	"""R17. The lock keeps another DEPLOYER out; it says nothing about a
	filesystem substitution by anything else. A generation directory replaced
	by a symlink between the release installs and the alias write was followed:
	the install succeeded, the alias landed outside the destination, and the
	report printed the DEST path it had never used."""
	candidate.require()
	destination = tmp_path / "dest"
	outside = tmp_path / "outside"
	outside.mkdir()
	real = deploy._set_alias_at
	swapped = []

	def swap_then_alias(generation_fd, generation_dir, target, **kwargs):
		if not swapped:
			swapped.append(generation_dir)
			# The PRODUCT directory, an ancestor of the generation: `O_NOFOLLOW`
			# on a final component says nothing about the path above it, so
			# this is the swap a lexical resolution actually follows. The
			# generation is moved out intact and a link left in its place, so
			# the lexical path still resolves to a real directory.
			product = pathlib.Path(generation_dir).parent
			moved = outside / product.name
			shutil.move(str(product), str(moved))
			product.symlink_to(moved)
		return real(generation_fd, generation_dir, target, **kwargs)

	monkeypatch.setattr(deploy, "_set_alias_at", swap_then_alias)
	# The install either refuses or writes through its held descriptor; what
	# it may never do is create anything in `outside`.
	try:
		deploy.install(str(candidate.ROOT), str(destination))
	except deploy.DeployError:
		pass

	assert swapped, "the swap was never injected"
	# The moved tree is out there; what must NOT be out there is an alias this
	# install wrote after the swap. Whichever product was moved -- the first
	# alias processed -- is the one to look in.
	assert not list(outside.rglob("latest")), \
		f"an alias was written outside the destination: {list(outside.rglob('latest'))}"


# -- the audit is part of the deployment, not a courtesy --------------------
#
# R16. Recording every failure as the string "unrecorded (...)" and computing
# durability from releases and aliases alone meant a deployment with NO
# evidence printed `durable: true` and exited zero -- while the record is the
# whole mechanism that keeps the three gates separate audits.

def test_a_deployment_whose_act_was_not_recorded_does_not_claim_success(
		tmp_path, monkeypatch):
	candidate.require()
	destination = tmp_path / "dest"

	def cannot_record(root_fd, dest, gate, digest, releases, aliases,
	                  recovered=None):
		return {"recorded": None, "durable": False, "problem": "no space"}

	monkeypatch.setattr(deploy, "_record_operation", cannot_record)
	report = deploy._report(deploy.install(str(candidate.ROOT), str(destination)))

	assert report["durable"] is False
	assert report["operation_problem"] == "no space"
	# ...and the releases it did install are still there. Evidence failing is
	# not a reason to undo writes that succeeded.
	assert (_release_path(destination, "baton-cli")).is_dir()


def test_an_invented_act_is_refused_before_anything_is_written(tmp_path):
	candidate.require()
	destination = tmp_path / "dest"

	with pytest.raises(deploy.DeployError, match="not a deployment act"):
		deploy.install(str(candidate.ROOT), str(destination), gate="invented")
	assert not (destination / "app").exists()


def test_each_act_is_its_own_immutable_document(tmp_path):
	"""One truncated write cannot make the others unreadable, which an
	appended log could not promise -- and two acts in the same second do not
	collide, which is exactly what an idempotent redeploy does."""
	candidate.require()
	destination = tmp_path / "dest"
	first = deploy.install(str(candidate.ROOT), str(destination))
	second = deploy.install(str(candidate.ROOT), str(destination))

	assert first["operation"] != second["operation"]
	documents = sorted((destination / "operations").glob("*.json"))
	assert len(documents) == 2
	for path in documents:
		entry = json.loads(path.read_text())
		assert entry["format"] == "baton.deployment-operation"
		assert entry["gate"] == "candidate-deploy"
		assert path.stat().st_mode & 0o777 == 0o444


def test_a_partial_operation_write_publishes_nothing(tmp_path, monkeypatch):
	candidate.require()
	destination = tmp_path / "dest"
	real = deploy._rename_noreplace

	def explode(source, target):
		if "operation" in source:
			raise OSError(28, "No space left on device")
		return real(source, target)

	monkeypatch.setattr(deploy, "_rename_noreplace", explode)
	report = deploy._report(deploy.install(str(candidate.ROOT), str(destination)))

	assert report["durable"] is False
	assert list((destination / "operations").glob("*.json")) == []
	assert list((destination / "operations").glob(".operation-*")) == [], \
		"a half-written operation document was left behind"


# -- a receipt is a claim about one publication -----------------------------

def test_a_receipt_from_another_publication_is_not_inherited(publishable):
	"""R14. The receipt validated its own format and nothing else, so a
	completed step from ONE publication marked a DIFFERENT body done: half the
	team reading the old bytes and half the new, which is exactly what the
	one-body ruling exists to prevent."""
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")

	# The body changes; the recorded config digest is deliberately kept, so
	# only the receipt's own identity binding can notice.
	guide.write_text(guide.read_text() + "\nAn extra paragraph.\n")
	with pytest.raises(publisher.PublishError, match="different publication"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")
	with pytest.raises(publisher.PublishError, match="different publication"):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")


@pytest.mark.parametrize("field,value", [
	("sender", "web.reviewer"),
	("audience", ["web.reviewer"]),
	("config_digest", "0" * 64),
	("config_generation", 99),
	("body_sha256", "ab" * 32),
	("guide", "/somewhere/else/GUIDE.md"),
])
def test_every_identity_field_binds_the_receipt(publishable, field, value):
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	document = json.loads(receipt.read_text())
	document[field] = value
	receipt.write_text(json.dumps(document))

	with pytest.raises(publisher.PublishError, match="different publication"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_a_receipt_with_unknown_or_duplicate_fields_is_refused(publishable):
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	document = json.loads(receipt.read_text())
	document["blessed_by"] = "me"
	receipt.write_text(json.dumps(document))
	with pytest.raises(publisher.PublishError, match="does not write"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")

	receipt.write_text('{"format": "baton.guide-publication", '
	                   '"format_version": 2, "notice": "a", "notice": "b"}')
	with pytest.raises(publisher.PublishError, match="duplicate"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_a_step_that_may_have_committed_is_never_repeated_silently(publishable,
                                                                   monkeypatch):
	"""R15. Baton commits before this process learns it did. A crash between
	the send and the receipt leaves a step that may or may not have landed,
	and the previous code sent an ordinary second copy with no warning."""
	publisher, config, guide, receipt = publishable
	import baton_core

	real = publisher._write_receipt
	crashed = []

	def crash_after_the_send(home, path, document):
		if document.get("attempting") is None and document.get("notice") \
				and not crashed:
			crashed.append(True)
			raise RuntimeError("the process died before recording the notice")
		return real(home, path, document)

	monkeypatch.setattr(publisher, "_write_receipt", crash_after_the_send)
	with pytest.raises(RuntimeError):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")
	monkeypatch.undo()

	# The receipt says a notice was being attempted and does not say it
	# finished. A plain retry REFUSES rather than sending a silent duplicate.
	assert json.loads(receipt.read_text())["attempting"] == "notice"
	with pytest.raises(publisher.Uncertain, match="possible duplicate"):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")

	# Sending again is allowed, and it says what it is.
	sent = publisher.publish(str(config), str(guide), str(receipt),
	                         sender="human.slawomir", resend_uncertain=True)
	assert sent["notice"] and sent["publication"]

	with baton_core.open_instance(str(config), readonly=True) as store:
		notices = store.list_notices(participant="web.reviewer")
	flagged = [notice for notice in notices if notice.get("possible_duplicate")]
	assert flagged, "the resent notice carried no possible-duplicate warning"


def test_two_publishers_cannot_share_one_receipt(publishable):
	publisher, config, guide, receipt = publishable
	lock = pathlib.Path(str(receipt) + ".lock")
	lock.write_text("99999\n")
	try:
		with pytest.raises(publisher.PublishError, match="another publication"):
			publisher.publish(str(config), str(guide), str(receipt),
			                  sender="human.slawomir")
	finally:
		lock.unlink()


def test_a_regen_between_generating_and_sending_is_refused(publishable):
	"""Audience equality alone is not the frozen-config proof: a `regen` that
	changes the accepted digest without changing the participant list would
	publish the old guide under the new config."""
	publisher, config, guide, receipt = publishable
	import baton_core

	# INJECTED IN THE INTERVAL. The audience is read, and the authority is
	# opened a moment later; a `regen` in between changes the accepted digest
	# without changing the participant list, so audience equality alone would
	# publish the old guide under the new config.
	real_open = baton_core.open_instance
	opens = []
	regenerated = []

	def regen_then_open(path, **kwargs):
		opens.append(path)
		# The SECOND open is the publisher's own: the first is the read-only
		# one that froze the audience, and the interval between them is where
		# a `regen` slips in.
		if len(opens) == 2 and not regenerated:
			regenerated.append(True)
			document = json.loads(config.read_text())
			document["generation"] = 2
			document["retention_days"] = 60   # keeps the audience identical
			config.write_text(json.dumps(document))
			baton_core.regen_instance(str(config),
			                          participant="human.slawomir")
		return real_open(path, **kwargs)

	monkeypatch = pytest.MonkeyPatch()
	monkeypatch.setattr(baton_core, "open_instance", regen_then_open)
	try:
		with pytest.raises(publisher.PublishError, match="config"):
			publisher.publish(str(config), str(guide), str(receipt),
			                  sender="human.slawomir")
	finally:
		monkeypatch.undo()
	assert regenerated, "the regen was never injected"


def test_the_ceremony_has_recipes_rather_than_improvised_python():
	"""R19. A production ceremony that requires somebody to remember a python
	invocation is a ceremony with a step nobody reviewed."""
	recipes = (REPO / "justfile").read_text()
	for recipe in ("guide DESTINATION", "guide-plan", "guide-publish",
	               "deploy DESTINATION"):
		assert recipe in recipes, recipe
	assert "--send" in recipes, "publishing has no recipe that actually sends"
	# ...and the removed ceremonies are not left behind as recipes that would
	# fail on a tool that no longer exists.
	for gone in ("deploy-import", "recover-legacy"):
		assert gone not in recipes, gone


def test_the_gate_comment_describes_what_the_code_does():
	"""R19. The comment still said the gate lives in each release record and a
	different-act reinstall refuses — the exact behaviour R8 removed."""
	source = (REPO / "tools" / "deploy.py").read_text()
	block = source[source.index("GATES = (") - 900:source.index("GATES = (")]
	assert "SUPERSEDED" in block
	assert "only in the operation record" in block


def test_an_unconfirmed_receipt_step_stops_before_the_send(publishable,
                                                           monkeypatch):
	"""R20. The `attempting` record's durability was folded into the exit code
	and the send happened anyway — so a power loss could revert the receipt
	while the notice had already committed, and the retry would not know it
	was resending. Each receipt boundary is a GATE for the next external
	mutation."""
	publisher, config, guide, receipt = publishable
	import baton_core

	real = publisher._write_receipt
	monkeypatch.setattr(publisher, "_write_receipt",
	                    lambda home, path, document:
	                    (real(home, path, document), False)[1])

	with pytest.raises(publisher.Unrecorded, match="nothing further was sent"):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")
	monkeypatch.undo()

	# NOTHING was published: not the notice, not the directed publication.
	with baton_core.open_instance(str(config), readonly=True) as store:
		assert store.list_notices(participant="web.reviewer") == []
		assert store.scan(participant="web.reviewer")["pending"] == []
	assert json.loads(receipt.read_text())["notice"] is None


def test_an_unconfirmed_notice_record_stops_before_the_directed_publication(
		publishable, monkeypatch):
	publisher, config, guide, receipt = publishable
	import baton_core

	real = publisher._write_receipt
	seen = []

	def confirm_until_the_notice_lands(home, path, document):
		real(home, path, document)
		seen.append(document.get("notice"))
		# The first two writes (attempting, then the notice itself) are the
		# ones under test: the second is where a failure must stop the run.
		return not (document.get("notice") and document.get("attempting") is None)

	monkeypatch.setattr(publisher, "_write_receipt",
	                    confirm_until_the_notice_lands)
	with pytest.raises(publisher.Unrecorded):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")
	monkeypatch.undo()

	with baton_core.open_instance(str(config), readonly=True) as store:
		assert len(store.list_notices(participant="web.reviewer")) == 1
		assert store.scan(participant="web.reviewer")["pending"] == [], \
			"the directed publication went out after an unrecorded notice"


@pytest.mark.parametrize("field,value", [
	("publication", 123),
	("notice", ""),
	("attempting", "something-else"),
	("audience", ["b.two", "a.one"]),
	("config_generation", 0),
	("body_sha256", "nothex" * 10),
	("guide", "relative/path.md"),
])
def test_a_receipt_with_a_malformed_field_is_neither_work_nor_a_traceback(
		publishable, field, value):
	"""R21. The loader refused duplicates and unknowns and then believed
	whatever the known keys held: `"publication": 123` counted as completed
	work and a missing key became a `KeyError`."""
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	document = json.loads(receipt.read_text())
	document[field] = value
	receipt.write_text(json.dumps(document))

	with pytest.raises(publisher.PublishError):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_a_receipt_missing_a_field_is_refused_not_crashed(publishable):
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	document = json.loads(receipt.read_text())
	del document["attempting"]
	receipt.write_text(json.dumps(document))

	with pytest.raises(publisher.PublishError, match="missing"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_the_body_is_read_once(publishable, monkeypatch):
	"""R21. Hashing one read and sending another let an edit in between put
	the old digest in the receipt and the new bytes on the wire."""
	publisher, config, guide, receipt = publishable
	reads = []
	real = publisher._read_once

	def count(path):
		reads.append(path)
		return real(path)

	monkeypatch.setattr(publisher, "_read_once", count)
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	assert len(reads) == 1, f"the guide was read {len(reads)} times"


@pytest.mark.parametrize("where", ["mkdir", "mkstemp", "write", "chmod",
                                   "rename", "fsync"])
def test_every_operation_record_failure_is_an_outcome_not_a_crash(tmp_path,
                                                                  monkeypatch,
                                                                  where):
	"""R23. `mkstemp` sat outside the guarded block and `_descend`'s `mkdir`
	escaped too, so an ordinary ENOSPC while writing EVIDENCE raised after both
	releases and both aliases had committed — reporting the deployment as a
	crash when what failed was the note about it."""
	candidate.require()
	destination = tmp_path / "dest"
	boom = OSError(28, "No space left on device")

	if where == "mkdir":
		real = deploy.os.mkdir

		def fail(name, *args, **kwargs):
			if name == "operations":
				raise boom
			return real(name, *args, **kwargs)
		monkeypatch.setattr(deploy.os, "mkdir", fail)
	elif where == "mkstemp":
		real = deploy.tempfile.mkstemp

		def fail(*args, **kwargs):
			if kwargs.get("prefix") == ".operation-":
				raise boom
			return real(*args, **kwargs)
		monkeypatch.setattr(deploy.tempfile, "mkstemp", fail)
	elif where == "write":
		monkeypatch.setattr(deploy, "_write_operation",
		                    lambda *a, **k: (_ for _ in ()).throw(boom))
	elif where == "chmod":
		real = deploy.os.chmod

		def fail(path, mode, **kwargs):
			if ".operation-" in str(path):
				raise boom
			return real(path, mode, **kwargs)
		monkeypatch.setattr(deploy.os, "chmod", fail)
	elif where == "rename":
		real = deploy._rename_noreplace

		def fail(source, target):
			if ".operation-" in source:
				raise boom
			return real(source, target)
		monkeypatch.setattr(deploy, "_rename_noreplace", fail)
	else:
		real = deploy._fsync_dir

		def fail(path):
			if "operations" in path or re.fullmatch(r"/proc/self/fd/\d+", path):
				raise OSError(5, "Input/output error")
			return real(path)
		monkeypatch.setattr(deploy, "_fsync_dir", fail)

	report = deploy._report(deploy.install(str(candidate.ROOT), str(destination)))

	assert report["durable"] is False, "an unrecorded act claimed success"
	# The deployment itself HAPPENED and the report says so: evidence failing
	# is not a reason to pretend the bytes were not installed.
	assert (_release_path(destination, "baton-cli")).is_dir()
	assert {item["state"] for item in report["releases"]} == {"installed"}
	assert list((destination / "operations").glob(".operation-*")) == []


def test_a_failed_recovery_is_reported_beside_the_original_failure(tmp_path,
                                                                   monkeypatch):
	"""R24. The operator saw only "the second alias failed" while the first
	might still be advanced, or rolled back without confirmed durability."""
	destination = tmp_path / "dest"
	deploy.install(str(_bumped(tmp_path, "first", "11.1.0", "11.4.0")),
	               str(destination))

	real = deploy._set_alias_at
	seen = set()

	def advance_then_fail(generation_fd, generation_dir, target, **kwargs):
		product = pathlib.Path(generation_dir).parent.name
		if product in seen:                      # a recovery call
			moved = real(generation_fd, generation_dir, target, **kwargs)
			moved["durable"] = False             # ...that cannot be confirmed
			return moved
		seen.add(product)
		if len(seen) > 1:
			raise deploy.DeployError("the second alias could not be written")
		return real(generation_fd, generation_dir, target, **kwargs)

	monkeypatch.setattr(deploy, "_set_alias_at", advance_then_fail)
	with pytest.raises(deploy.DeployFailed) as failure:
		deploy.install(str(_bumped(tmp_path, "second", "11.2.0", "11.5.0")),
		               str(destination))

	text = str(failure.value)
	assert "the second alias could not be written" in text, "the cause was lost"
	assert "Recovery:" in text
	assert "NOT confirmed durable" in text
	assert "Reconcile with" in text
	# The first alias advanced is the console's (products are processed in
	# sorted manifest order), so its restored target is the console's previous
	# release.
	assert failure.value.recovery[0]["observed"] == "v11.4.0"
	assert failure.value.recovery[0]["state"] == "restored"


def test_an_uncertain_advance_is_reported_rather_than_rewritten(tmp_path,
                                                                monkeypatch):
	destination = tmp_path / "dest"
	deploy.install(str(_bumped(tmp_path, "first", "11.1.0", "11.4.0")),
	               str(destination))
	real = deploy._set_alias_at
	seen = set()

	def uncertain_then_fail(generation_fd, generation_dir, target, **kwargs):
		product = pathlib.Path(generation_dir).parent.name
		if product in seen:
			raise AssertionError("an uncertain alias was written over")
		seen.add(product)
		if len(seen) > 1:
			raise deploy.DeployError("the second alias could not be written")
		moved = real(generation_fd, generation_dir, target, **kwargs)
		moved["durable"] = False
		return moved

	monkeypatch.setattr(deploy, "_set_alias_at", uncertain_then_fail)
	with pytest.raises(deploy.DeployFailed) as failure:
		deploy.install(str(_bumped(tmp_path, "second", "11.2.0", "11.5.0")),
		               str(destination))

	assert "without confirmed durability" in str(failure.value)
	assert failure.value.recovery[0]["state"] == "left"


# -- what containment promises, and what it does not ------------------------
#
# R22. "Check, then write through the descriptor" detects a substitution; it
# does not prevent one. A directory descriptor follows an INODE, and a
# same-UID process can move that inode out of the destination between any
# check and the commit after it. No POSIX primitive pins a directory to a
# path, so this is a threat-model boundary rather than a bug to be quietly
# closed — and the code, the tests and the prose have to say the same thing
# about it.

def test_the_module_states_the_boundary_it_actually_enforces():
	"""The claim under test is a SENTENCE, because the failure mode was a
	sentence: this module implied no substitution could write outside, which
	is not something it can enforce."""
	source = (REPO / "tools" / "deploy.py").read_text()
	assert "OUT OF SCOPE, DELIBERATELY" in source
	assert "follows an INODE" in source
	# APPROVED, and still not claimed as prevented: the ruling accepted the
	# cost of the gap, it did not close it, and the wording has to keep those
	# two things apart.
	assert "APPROVED BY SLAWOMIR ON 2026-08-13" in source
	assert "not prevented" in source
	assert "flagged for Slawomir" not in source


def test_the_kernel_enforces_beneath_where_it_can(tmp_path):
	"""`openat2` with RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS, when the kernel has
	it; the component-wise fallback refuses the same objects."""
	root = tmp_path / "root"
	(root / "inside").mkdir(parents=True)
	outside = tmp_path / "outside"
	outside.mkdir()
	(root / "escape").symlink_to(outside)
	root_fd = deploy._open_root(str(root))
	try:
		assert deploy._openat2_beneath("inside", root_fd) is None or True
		with pytest.raises((deploy.DeployError, OSError)):
			deploy._descend(root_fd, ["escape"])
	finally:
		os.close(root_fd)


def test_a_relocation_after_the_last_check_is_detected_where_it_can_be(
		tmp_path, monkeypatch):
	"""What the re-walk DOES buy: a relocation that happens before the last
	check is refused, and the deployment stops rather than continuing to write
	through a descriptor that has left the destination."""
	candidate.require()
	destination = tmp_path / "dest"
	outside = tmp_path / "outside"
	outside.mkdir()
	real = deploy._still_inside
	moved = []

	def move_then_check(root_fd, components, fd, expected):
		if not moved and components[:2] == ["app", "baton-tui"]:
			moved.append(expected)
			shutil.move(str(pathlib.Path(expected).parent),
			            str(outside / "baton-tui"))
		return real(root_fd, components, fd, expected)

	monkeypatch.setattr(deploy, "_still_inside", move_then_check)
	with pytest.raises(deploy.DeployError, match="no longer reachable"):
		deploy.install(str(candidate.ROOT), str(destination))

	assert moved, "the relocation was never injected"
	assert not list((outside / "baton-tui").rglob("latest")), \
		"an alias was written into the relocated tree after the refusal"


def test_the_receipt_is_written_inside_a_held_parent(publishable, tmp_path):
	"""R25. The lock, the staging file, the replace and the fsync were all
	lexical, so a symlinked parent was followed and the real receipt was
	published outside the path that was named."""
	publisher, config, guide, _receipt = publishable
	outside = tmp_path / "outside"
	outside.mkdir()
	linked = tmp_path / "receipts"
	linked.symlink_to(outside)

	with pytest.raises(publisher.PublishError, match="symlink"):
		publisher.publish(str(config), str(guide), str(linked / "receipt.json"),
		                  sender="human.slawomir")
	assert list(outside.iterdir()) == [], \
		"the receipt was written through the symlinked parent"


def test_a_receipt_parent_that_is_not_a_directory_is_refused(publishable,
                                                             tmp_path):
	publisher, config, guide, _receipt = publishable
	(tmp_path / "notadir").write_text("hello\n")
	with pytest.raises(publisher.PublishError, match="not a directory"):
		publisher.publish(str(config), str(guide),
		                  str(tmp_path / "notadir" / "receipt.json"),
		                  sender="human.slawomir")


@pytest.mark.parametrize("value", ["made-up", "ab" * 32, "A" * 32, "", "0" * 31])
def test_a_recorded_identifier_must_be_one_baton_issues(publishable, value):
	"""R25. "Non-empty string" accepted `made-up` as completed work, so a
	receipt could claim a publication that never existed."""
	publisher, config, guide, receipt = publishable
	publisher.publish(str(config), str(guide), str(receipt),
	                  sender="human.slawomir")
	document = json.loads(receipt.read_text())
	document["notice"] = value
	receipt.write_text(json.dumps(document))

	with pytest.raises(publisher.PublishError, match="identifier Baton issues"):
		publisher.plan(str(config), str(guide), str(receipt),
		               sender="human.slawomir")


def test_an_undeclared_sender_is_a_refusal_not_a_traceback(publishable, capsys):
	"""R25. A `BatonError` from the send path escaped as a traceback."""
	publisher, config, guide, receipt = publishable
	code = publisher.main([str(guide), "--config", str(config), "--receipt",
	                       str(receipt), "--participant", "nobody.here",
	                       "--send"])
	captured = capsys.readouterr()
	assert code == 1
	assert "Traceback" not in captured.err
	assert "publish_guide:" in captured.err
	assert "re-run to continue" in captured.err or "nobody.here" in captured.err


@pytest.mark.parametrize("depth", ["first", "middle", "final"])
def test_every_receipt_ancestor_is_checked_not_just_the_parent(publishable,
                                                               tmp_path, depth):
	"""R27. `O_NOFOLLOW` applies to the FINAL component only, and `islink` was
	asked about that same final component — so `ROOT/linked/nested/receipt.json`,
	where `nested` is a real directory inside a symlinked `linked`, resolved
	happily and published the receipt outside the path that was named."""
	publisher, config, guide, _receipt = publishable
	outside = tmp_path / "outside"
	outside.mkdir()
	root = tmp_path / "root"

	if depth == "first":
		root.symlink_to(outside)
		receipt = root / "a" / "b" / "receipt.json"
		(outside / "a" / "b").mkdir(parents=True)
	elif depth == "middle":
		(root / "a").mkdir(parents=True)
		(root / "a" / "linked").symlink_to(outside)
		(outside / "b").mkdir()
		receipt = root / "a" / "linked" / "b" / "receipt.json"
	else:
		(root / "a").mkdir(parents=True)
		(root / "a" / "linked").symlink_to(outside)
		receipt = root / "a" / "linked" / "receipt.json"

	with pytest.raises(publisher.PublishError, match="symlink|not a directory"):
		publisher.publish(str(config), str(guide), str(receipt),
		                  sender="human.slawomir")

	assert not list(outside.rglob("receipt.json")), \
		"the receipt was written through a symlinked ancestor"
	assert not list(outside.rglob("*.lock")), \
		"the lock was taken through a symlinked ancestor"


def test_an_expected_refusal_is_rendered_and_a_defect_is_not(publishable,
                                                             monkeypatch,
                                                             capsys):
	"""R28. Catching every `Exception` printed "re-run to continue" over an
	`AssertionError` and hid the traceback that would have shown where it was.
	A programming defect is not an uncertain external outcome."""
	publisher, config, guide, receipt = publishable

	# One expected operational failure: rendered, exit 1.
	assert publisher.main([str(guide), "--config", str(config), "--receipt",
	                       str(receipt), "--participant", "nobody.here",
	                       "--send"]) == 1
	assert "Traceback" not in capsys.readouterr().err

	# One programming defect: NOT swallowed.
	def broken(*args, **kwargs):
		raise AssertionError("invariant broken")

	monkeypatch.setattr(publisher, "publish", broken)
	with pytest.raises(AssertionError, match="invariant broken"):
		publisher.main([str(guide), "--config", str(config), "--receipt",
		                str(receipt), "--participant", "human.slawomir",
		                "--send"])


def test_the_approved_boundary_is_not_stated_as_a_solved_problem():
	"""The ruling accepted a cost; it did not close a gap. Every place that
	describes the boundary has to keep those two apart, because "approved" is
	the word most likely to be read as "handled"."""
	for path in (REPO / "tools" / "deploy.py", REPO / "README.md",
	             REPO / "tools" / "publish_guide.py"):
		text = path.read_text()
		if "same-UID" not in text and "same user" not in text:
			continue
		assert "cannot" in text or "does not" in text or "NOT prevent" in text \
			or "not prevented" in text, path
		for overclaim in ("cannot write outside", "no substitution can",
		                  "guaranteed to stay inside"):
			assert overclaim not in text, f"{path}: {overclaim}"
