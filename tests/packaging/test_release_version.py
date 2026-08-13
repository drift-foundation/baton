"""Independently versioned products, each reporting itself, offline.

SUPERSEDED PREMISE, kept because it is why these tests exist at all. This file
used to pin ONE release version reported by both executables: the pre-release
numbers had drifted on purpose -- the CLI counted its own revisions to 6.0.0
while the console sat at 0.2.0 -- and shipping two numbers for one thing, with
nothing saying which a human should quote, was the failure being prevented.

Slawomir ruled on 2026-08-12 that `baton`, `baton-tui` and `baton_core` are
independently versioned products. The old rule prevented drift by making
difference impossible; the new one permits deliberate difference and prevents
ACCIDENTAL drift by giving every version exactly one owner -- the catalog at
`src/baton_core/products.json`. So what these tests pin changed shape: not
"every surface says the same number" but "no surface holds its own copy of any
number".

SUPERSEDED AGAIN, 2026-08-12: the currency check used to be measured against
the CHECKED-IN artifacts and was expected to fail while 1.1 source sat beside
frozen 1.0 binaries. A build no longer writes to the checkout, so those bytes
are historical inputs and comparing them with current source would be asking
whether history had changed. Currency now means the CANDIDATE under `build/`
matches its own source: the check rebuilds into a scratch root and compares
bytes. It reads the candidate and never writes one -- `just build` prepares
it, and a gate that manufactured what it inspects would report on bytes nobody
chose to release.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import baton_core
from baton_core import products

import candidate

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "src"
TOOLS = REPO / "tools"
# THE CANDIDATE, not the checkout. A build no longer replaces the executables
# live consumers run, so "the released bytes" are the ones under `build/` and
# the checkout's `bin/`+`dist/` are historical inputs rather than outputs.
DIST = candidate.DIST
CLI = candidate.CLI
TUI = candidate.TUI

PROTOCOL = baton_core.PROTOCOL_VERSION
CLI_VERSION = products.CLI_VERSION
TUI_VERSION = products.TUI_VERSION

CLI_LINE = f"baton {CLI_VERSION} (protocol {PROTOCOL})"
TUI_LINE = f"baton-tui {TUI_VERSION} (protocol {PROTOCOL})"


def _candidates(root: pathlib.Path):
	"""Build both products into a scratch root and return their manifests.

	Never `bin/` and never `build/`: the checkout's artifacts are historical
	inputs a build no longer writes, and the shared candidate is the thing
	these gates report on -- a test that rebuilt either would be examining its
	own output."""
	root.mkdir(exist_ok=True)
	for builder in ("build_zipapp.py", "build_tui.py"):
		built = subprocess.run([sys.executable, str(TOOLS / builder), str(root)],
		                       capture_output=True)
		assert built.returncode == 0, (builder, built.stderr)
	return (json.loads((root / "dist" / "DISTRIBUTION.json").read_text()),
	        json.loads((root / "dist" / "DISTRIBUTION-TUI.json").read_text()))


# -- the catalog is the one owner -----------------------------------------

def test_every_version_has_exactly_one_declaration():
	"""The literals live HERE and nowhere else: every other surface derives
	them, so a release changes the catalog and this one test."""
	catalog = products.catalog()
	assert catalog["format"] == "baton.products"
	assert catalog["format_version"] == 1
	assert catalog["core"]["version"] == "1.2.0"
	assert catalog["core"]["api_version"] == 4
	assert catalog["protocol_version"] == 10
	# THE APPLICATION MAJOR IS THE PROTOCOL, ruled 2026-08-13. The core keeps
	# its own line -- it is embedded, not deployed into a generation -- which
	# is why these three numbers no longer march together.
	assert catalog["products"]["baton"]["version"] == "10.2.0"
	assert catalog["products"]["baton-tui"]["version"] == "10.2.0"
	assert catalog["products"]["baton"]["version"].split(".")[0] == \
		str(catalog["protocol_version"])
	for name in ("baton", "baton-tui"):
		assert catalog["products"][name]["requires_core_api"] == 4

	# Semantic, and checked as such: these strings are compared, printed and
	# used to name a release document.
	for version in (products.CORE_VERSION, CLI_VERSION, TUI_VERSION):
		parts = version.split(".")
		assert len(parts) == 3 and all(p.isdigit() for p in parts), version


def test_the_retired_shared_declaration_is_gone_not_aliased():
	"""A name that still resolves is a name something keeps using. There is no
	shared release version any more, so there is no `RELEASE_VERSION`."""
	assert not hasattr(baton_core, "RELEASE_VERSION")
	assert not hasattr(baton_core._impl, "RELEASE_VERSION")
	import baton_tui
	assert not hasattr(baton_core, "TOOL_VERSION")
	# ...and the console DOES carry its own version now, which is the change.
	assert baton_tui.TUI_VERSION == TUI_VERSION
	assert baton_core.CORE_VERSION == products.CORE_VERSION
	assert baton_core._impl.CLI_VERSION == CLI_VERSION


def test_the_core_api_reports_the_core_package_version():
	"""`core_versions()` is what a front end checks at startup. It names the
	core's own version now; `tool_version` is gone with the shared release it
	answered for."""
	versions = baton_core.core_versions()
	assert versions == {"core_api_version": 4,
	                    "core_version": products.CORE_VERSION,
	                    "protocol_version": PROTOCOL}
	assert "tool_version" not in versions


def _catalog_with(**changes):
	"""The real catalog with one thing wrong, so each case tests one rule."""
	document = products.catalog()
	for path, value in changes.items():
		target = document
		*parents, leaf = path.split("__")
		for step in parents:
			target = target[step]
		if value is None:
			target.pop(leaf, None)
		else:
			target[leaf] = value
	return document


@pytest.mark.parametrize("document,expected", [
	({}, "not 'baton.products'"),
	(_catalog_with(format_version=99), "format version"),
	(_catalog_with(protocol_version=None), "protocol_version"),
	(_catalog_with(protocol_version="ten"), "protocol_version"),
	(_catalog_with(core=None), "no core section"),
	(_catalog_with(core__version="1.1"), "not major.minor.patch"),
	(_catalog_with(core__version="one.one.oh"), "not major.minor.patch"),
	(_catalog_with(core__api_version="3"), "api_version is not an integer"),
	(_catalog_with(floors=None), "no floors section"),
	(_catalog_with(floors__python_min=None), "floors.python_min"),
	(_catalog_with(products=None), "lists no products"),
	(_catalog_with(products={}), "lists no products"),
])
def test_a_damaged_catalog_is_refused_rather_than_guessed(tmp_path, monkeypatch,
                                                          document, expected):
	"""Every refusal here exists because the alternative is a plausible-looking
	default: a missing version reported as `None`, an unknown format read as
	this one, a version string that is not a version reaching a release
	document's filename."""
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))
	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	try:
		products._load()
	except products.CatalogError as refusal:
		assert expected in str(refusal), (expected, str(refusal))
	else:                                              # pragma: no cover
		raise AssertionError(f"{document} was accepted")


@pytest.mark.parametrize("version", ["1.1", "1.1.0.0", "one.one.oh", "v1.1.0", "",
                                     "01.2.3", "1.02.3", "1.2.03"])
def test_a_product_version_that_is_not_semantic_is_refused(tmp_path, monkeypatch,
                                                           version):
	"""A product version names a release document and is compared and printed.
	Every one of those is worse with a typo in it than without.

	The leading-zero cases matter for a specific reason: `01.2.3` is all
	digits, so an `isdigit` check accepted it here and the deployer refused it
	at publication. A builder must not succeed at producing an artifact its own
	deployer necessarily rejects, so both use the same spelling now."""
	document = products.catalog()
	document["products"]["baton"]["version"] = version
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))
	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	try:
		products._load()
	except products.CatalogError as refusal:
		assert "products.baton.version" in str(refusal), str(refusal)
	else:                                              # pragma: no cover
		raise AssertionError(f"{version!r} was accepted")


# -- what each executable says about itself --------------------------------

def test_both_source_parsers_answer_version_and_advertise_it_in_help():
	"""Evidence 1: the argument surface, before any packaging. Each parser
	names ITS OWN product."""
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
		assert "print this product's version and exit" in help_text


def test_the_two_products_are_reported_independently(monkeypatch):
	"""The point of the ruling, asserted as behaviour rather than as a
	possibility: with different numbers in the catalog, each executable reports
	its own and neither borrows the other's."""
	import contextlib
	import importlib
	import io

	catalog = products.catalog()
	catalog["products"]["baton"]["version"] = "1.1.0"
	catalog["products"]["baton-tui"]["version"] = "1.4.0"
	monkeypatch.setattr(products, "_CATALOG", catalog)
	monkeypatch.setattr(products, "CLI_VERSION", "1.1.0")
	monkeypatch.setattr(products, "TUI_VERSION", "1.4.0")

	from baton_core import _impl
	import baton_tui
	from baton_tui import driver
	monkeypatch.setattr(_impl, "CLI_VERSION", "1.1.0")
	monkeypatch.setattr(baton_tui, "TUI_VERSION", "1.4.0")

	lines = []
	for parser in (_impl._build_parser(), driver.build_parser()):
		out = io.StringIO()
		try:
			with contextlib.redirect_stdout(out):
				parser.parse_args(["--version"])
		except SystemExit:
			pass
		lines.append(out.getvalue().strip())
	assert lines == [f"baton 1.1.0 (protocol {PROTOCOL})",
	                 f"baton-tui 1.4.0 (protocol {PROTOCOL})"], lines


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


def test_both_packaged_executables_print_their_own_line(tmp_path):
	"""Evidence 2: built artifacts, not the source tree.

	No config, no terminal (`TERM` removed and the pipes are not a tty), no
	participant, no authority, no project directory -- an empty temporary
	directory is the whole world. Exactly one line, exit zero.

	This also proves the catalog SHIPS: a zipapp reading `products.json`
	through `importlib.resources` is the only reason these numbers exist
	outside a repository at all."""
	root = tmp_path / "root"
	_candidates(root)
	home = tmp_path / "home"
	home.mkdir()
	for artifact, expected in ((root / "bin" / "baton", CLI_LINE),
	                           (root / "bin" / "baton-tui", TUI_LINE)):
		run = _offline_run([sys.executable, str(artifact), "--version"], home)
		assert run.returncode == 0, (artifact.name, run.stderr)
		assert run.stdout.decode() == expected + "\n", run.stdout
		assert run.stderr == b"", run.stderr


def test_the_version_query_touches_no_store_config_or_project(tmp_path):
	"""Evidence 3: the tripwire.

	Three ways for the query to be doing more than it says: leaving something
	behind, reading a config, or refusing without one. A version query that
	created a store would pass the output test above and still be wrong."""
	root = tmp_path / "root"
	_candidates(root)
	for name, expected in (("baton", CLI_LINE), ("baton-tui", TUI_LINE)):
		artifact = root / "bin" / name
		home = tmp_path / f"home-{name}"
		home.mkdir()

		run = _offline_run([sys.executable, str(artifact), "--version"], home)
		assert run.returncode == 0, run.stderr
		# Nothing written: no store, no journal, no dotfile, no lock.
		assert sorted(p.name for p in home.iterdir()) == [], \
			sorted(p.name for p in home.iterdir())

		# A config path that does not exist must not even be looked at.
		missing = str(home / "nowhere" / "baton.json")
		named = _offline_run(
			[sys.executable, str(artifact), "--config", missing, "--version"], home)
		assert named.returncode == 0, named.stderr
		assert named.stdout.decode() == expected + "\n"
		assert sorted(p.name for p in home.iterdir()) == []


# -- generated attestations ------------------------------------------------

def test_both_manifests_derive_every_fact_from_the_catalog(tmp_path):
	"""Evidence 4: no surface may hold its own copy of a number."""
	cli_manifest, tui_manifest = _candidates(tmp_path / "root")

	assert cli_manifest["product_version"] == CLI_VERSION
	assert tui_manifest["product_version"] == TUI_VERSION
	assert cli_manifest["protocol_version"] == PROTOCOL
	assert tui_manifest["protocol_version"] == PROTOCOL
	for manifest in (cli_manifest, tui_manifest):
		assert manifest["requires_core_api"] == baton_core.CORE_API_VERSION
		assert manifest["python_min"] == products.PYTHON_MIN
		assert manifest["sqlite_min"] == products.SQLITE_MIN_TEXT
	# The retired shared key must not linger beside the per-product ones.
	assert "release_version" not in cli_manifest
	assert "release_version" not in tui_manifest


def test_both_products_attest_the_core_they_embed(tmp_path):
	"""The gap independent cadences make dangerous: a console shipped against a
	core it was not built for. The manifest could not say which core it carried
	at all before this."""
	root = tmp_path / "root"
	cli_manifest, tui_manifest = _candidates(root)

	for manifest in (cli_manifest, tui_manifest):
		core = manifest["embeds_core"]
		assert core["version"] == products.CORE_VERSION
		assert core["api_version"] == baton_core.CORE_API_VERSION
		assert len(core["package_sha256"]) == 64

	# Both products ship the SAME core, and now say so in a way a reader can
	# check rather than assume.
	assert cli_manifest["embeds_core"] == tui_manifest["embeds_core"]

	# And the attestation is over the bytes actually packaged: recomputing it
	# from the archive reproduces the manifest's digest.
	import hashlib
	import zipfile

	for manifest in (cli_manifest, tui_manifest):
		with zipfile.ZipFile(root / manifest["artifact"]) as archive:
			names = sorted(n for n in archive.namelist()
			               if n.startswith("baton_core/"))
			digest = hashlib.sha256()
			for name in names:
				digest.update(name.encode("utf-8"))
				digest.update(archive.read(name))
		assert digest.hexdigest() == manifest["embeds_core"]["package_sha256"]


def test_the_catalog_ships_inside_both_artifacts(tmp_path):
	"""It is data, not source, so nothing else would have packaged it -- and
	without it neither executable can say what it is."""
	import zipfile

	root = tmp_path / "root"
	_candidates(root)
	for name in ("baton", "baton-tui"):
		with zipfile.ZipFile(root / "bin" / name) as archive:
			assert "baton_core/products.json" in archive.namelist()
			shipped = json.loads(archive.read("baton_core/products.json"))
		assert shipped == products.catalog()


def test_the_readme_quotes_the_catalog(tmp_path):
	"""Documentation is a surface like any other: it may show the lines, but it
	may not become a second place the numbers are maintained."""
	readme = (REPO / "README.md").read_text()
	assert CLI_LINE in readme, CLI_LINE
	assert TUI_LINE in readme, TUI_LINE


def test_rebuilding_reproduces_the_candidate_artifacts_and_manifests(tmp_path):
	"""Evidence 5: the bytes in the CANDIDATE are the bytes this source builds.

	Built into a scratch root so the candidate is read, never rewritten, by a
	test.

	SUPERSEDED SUBJECT: this used to compare against the checked-in `bin/`, and
	was expected to fail whenever source moved ahead of the frozen artifacts --
	the currency gate that cleared only at a human release build. A build no
	longer writes to the checkout at all, so those bytes are historical inputs
	and comparing them to current source would be asking whether history has
	changed. What currency means now is that the candidate matches its own
	source, deterministically."""
	import hashlib

	# The candidate is READ here and built by `just build`. This is also the
	# staleness check the mtime rule used to make: a candidate that no longer
	# matches its own source fails on BYTES, not on a timestamp that a copy
	# preserves and a checkout resets.
	candidate.require()

	root = tmp_path / "root"
	root.mkdir()
	for builder in ("build_zipapp.py", "build_tui.py"):
		built = subprocess.run([sys.executable, str(TOOLS / builder), str(root)],
		                       capture_output=True)
		assert built.returncode == 0, (builder, built.stderr)

	for name, prepared in (("DISTRIBUTION.json", CLI),
	                       ("DISTRIBUTION-TUI.json", TUI)):
		manifest = json.loads((root / "dist" / name).read_text())
		rebuilt = root / manifest["artifact"]
		assert hashlib.sha256(rebuilt.read_bytes()).hexdigest() == \
			manifest["artifact_sha256"]
		assert rebuilt.read_bytes() == prepared.read_bytes(), manifest["artifact"]

		published = json.loads((DIST / name).read_text())
		assert published == manifest, name


def test_the_runtime_floor_comes_from_the_catalog(tmp_path, monkeypatch):
	"""R4. The floor used to be typed into both bootstrap strings and again
	into both manifests. Changing the catalog must move the executable's own
	refusal and the manifest that advertises it TOGETHER -- a manifest saying
	3.12 above a bootstrap refusing 3.10 is the same drift this design exists
	to remove, one size smaller."""
	import importlib
	import zipfile

	sys.path.insert(0, str(TOOLS))
	build_zipapp = importlib.import_module("build_zipapp")
	build_tui = importlib.import_module("build_tui")

	document = products.catalog()
	document["floors"]["python_min"] = "3.13"
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))

	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	reloaded = importlib.reload(products)
	try:
		monkeypatch.setattr(build_zipapp, "_catalog", lambda: reloaded)
		root = tmp_path / "root"
		root.mkdir()
		cli = build_zipapp.build(str(root))
		tui = build_tui.build(str(root))

		assert cli["python_min"] == "3.13"
		assert tui["python_min"] == "3.13"
		for name in ("baton", "baton-tui"):
			with zipfile.ZipFile(root / "bin" / name) as archive:
				bootstrap = archive.read("__main__.py").decode()
			assert "sys.version_info < (3, 13)" in bootstrap, name
			assert "required 3.13 floor" in bootstrap, name
			assert "(3, 11)" not in bootstrap, name
	finally:
		monkeypatch.undo()
		importlib.reload(products)


def test_a_catalog_whose_product_outruns_its_core_is_refused(tmp_path, monkeypatch):
	"""R4's other half. Every product embeds THIS core, so a catalog declaring
	a product that requires an API the core does not offer would build an
	artifact the deployer must refuse. A builder must not succeed at producing
	something its own deployer necessarily rejects."""
	document = products.catalog()
	# ONE PAST what this core offers, derived rather than typed: the number
	# moves with the core (3 -> 4 when the mailbox handshake landed), and a
	# hard-coded one stops being a mismatch the day the core reaches it.
	beyond = document["core"]["api_version"] + 1
	document["products"]["baton-tui"]["requires_core_api"] = beyond
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))
	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	try:
		products._load()
	except products.CatalogError as refusal:
		assert f"requires_core_api is {beyond}" in str(refusal), str(refusal)
		assert f"offers API {document['core']['api_version']}" in str(refusal), \
			str(refusal)
	else:                                              # pragma: no cover
		raise AssertionError("the mismatch was accepted")


@pytest.mark.parametrize("artifact", ["/bin/baton", "../escape/baton",
                                      "bin/../../out", "~/baton", "bin\\baton"])
def test_a_catalog_artifact_that_escapes_the_root_is_refused(tmp_path, monkeypatch,
                                                             artifact):
	document = products.catalog()
	document["products"]["baton"]["artifact"] = artifact
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))
	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	try:
		products._load()
	except products.CatalogError as refusal:
		assert "products.baton.artifact" in str(refusal), str(refusal)
	else:                                              # pragma: no cover
		raise AssertionError(f"{artifact!r} was accepted")


def test_two_catalog_products_cannot_name_one_artifact(tmp_path, monkeypatch):
	document = products.catalog()
	document["products"]["baton-tui"]["artifact"] = "bin/baton"
	catalog_dir = tmp_path / "catalog"
	catalog_dir.mkdir()
	(catalog_dir / "products.json").write_text(json.dumps(document))
	monkeypatch.setattr(products.resources, "files", lambda package: catalog_dir)
	try:
		products._load()
	except products.CatalogError as refusal:
		assert "is also" in str(refusal), str(refusal)
	else:                                              # pragma: no cover
		raise AssertionError("two products shared one artifact")
