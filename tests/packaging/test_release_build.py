"""One command prepares the WHOLE release set, or changes nothing.

`baton` and `baton-tui` are independently versioned but they are built from one
catalog and embed one core, and the deployer refuses a set whose products
disagree about either. Two commands made that coherence the human's job to
remember between them; Slawomir superseded that with one.

The failure this file is really about: building each product straight into the
repository meant a failure in the second left the first already replaced — a
new CLI beside an old console, both looking finished. So preparation happens in
a scratch root and nothing is installed until every product has built.

EVERY BUILD IN THIS SUITE TARGETS TEMPORARY STORAGE. The shared `build/`
candidate is prepared by `just build` and by nothing else; `just test` only
validates the candidate that command produced.

SUPERSEDED, and it is worth knowing why. This file used to say that
`test_the_default_target_is_the_candidate` deliberately refreshed the shared
candidate "which is what a build is for". It did refresh it -- with no
argument, `build()` resolved its definition-time default to the real
`build/` -- so every `just test` run rebuilt the tree it was reporting on. A
suite that manufactures its own subject is the exact thing the ruled `just
build` -> `just test` -> `just deploy` sequence exists to prevent, and it was
hiding inside the test that checks the sequence. That test now redirects
`CANDIDATE` to a temporary root before calling `build()` bare, so it still
proves the default follows the constant and touches nothing shared.

`test_no_test_can_target_the_shared_candidate` is what keeps that true for
tests nobody has written yet. The CHECKOUT's `bin/` and `dist/` are never
written by anything here, and
`test_building_leaves_the_checkout_executables_untouched` hashes them to prove
it.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(REPO / "src"))

import build_release                                   # noqa: E402


def _digest(path: pathlib.Path) -> str:
	return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def root(tmp_path):
	target = tmp_path / "release"
	target.mkdir()
	return target


def test_one_build_produces_the_complete_set(root):
	"""Both artifacts, both manifests, one command."""
	result = build_release.build(str(root))

	assert result["products"] == {"baton": "10.2.0", "baton-tui": "10.2.0"}
	for relative in ("bin/baton", "bin/baton-tui",
	                 "dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json"):
		assert (root / relative).is_file(), relative
		assert relative in result["installed"], relative

	for name, tool in (("DISTRIBUTION.json", "baton"),
	                   ("DISTRIBUTION-TUI.json", "baton-tui")):
		manifest = json.loads((root / "dist" / name).read_text())
		assert manifest["tool"] == tool
		assert _digest(root / manifest["artifact"]) == manifest["artifact_sha256"]


def test_the_set_is_coherent_by_construction(root):
	"""One catalog, one core, one protocol — checked by the build rather than
	left for the deployer to discover."""
	build_release.build(str(root))
	cli = json.loads((root / "dist" / "DISTRIBUTION.json").read_text())
	tui = json.loads((root / "dist" / "DISTRIBUTION-TUI.json").read_text())

	assert cli["embeds_core"] == tui["embeds_core"]
	assert cli["protocol_version"] == tui["protocol_version"]
	assert cli["requires_core_api"] == cli["embeds_core"]["api_version"]
	assert tui["requires_core_api"] == tui["embeds_core"]["api_version"]


def test_the_built_set_certifies(root, tmp_path):
	"""The point of building: what comes out is what the deployer accepts."""
	import shutil

	import deploy

	build_release.build(str(root))
	for name in ("README.md", "LICENSE", "examples/baton.json",
	             "docs/EFFECTIVE-BATON.md"):
		destination = root / name
		destination.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(REPO / name, destination)
	for tool, version in (("baton", "10.2.0"), ("baton-tui", "10.2.0")):
		(root / "docs" / f"RELEASE-{tool}-{version}.md").write_text(f"# {tool}\n")

	facts = deploy.certified(str(root))
	assert set(facts["products"]) == {"baton", "baton-tui"}
	assert len(facts["set_digest"]) == 64


def test_a_rebuild_is_byte_identical(root, tmp_path):
	"""Deterministic, so a release can be reproduced and compared."""
	other = tmp_path / "again"
	other.mkdir()
	build_release.build(str(root))
	build_release.build(str(other))
	for relative in ("bin/baton", "bin/baton-tui",
	                 "dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json"):
		assert (root / relative).read_bytes() == (other / relative).read_bytes(), \
			relative


# -- a failure may not leave a half-refreshed release tree -----------------

def test_a_failure_in_the_second_product_installs_nothing(root, monkeypatch):
	"""THE defect the aggregate build exists to prevent. Building each product
	straight into the tree left the first already replaced when the second
	failed: a new CLI beside an old console, both looking finished."""
	build_release.build(str(root))                      # an existing release
	# MARKED, because the build is deterministic: a second build produces
	# identical bytes, so installing the CLI would be invisible and the test
	# would pass on a build that had half-refreshed the tree.
	for relative in ("bin/baton", "bin/baton-tui",
	                 "dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json"):
		(root / relative).write_bytes(f"previous {relative}\n".encode())
	before = {relative: (root / relative).read_bytes()
	          for relative in ("bin/baton", "bin/baton-tui",
	                           "dist/DISTRIBUTION.json",
	                           "dist/DISTRIBUTION-TUI.json")}

	def explode(target):
		raise OSError(28, "No space left on device")
	monkeypatch.setattr(build_release.build_tui, "build", explode)

	with pytest.raises(OSError):
		build_release.build(str(root))

	for relative, content in before.items():
		assert (root / relative).read_bytes() == content, relative
	assert _staging_left_behind(root) == [], "a staging tree survived"


def test_a_failure_in_the_first_product_installs_nothing(root, monkeypatch):
	build_release.build(str(root))
	(root / "bin" / "baton-tui").write_bytes(b"previous console\n")
	before = (root / "bin" / "baton-tui").read_bytes()

	def explode(target):
		raise OSError(5, "Input/output error")
	monkeypatch.setattr(build_release.build_zipapp, "build", explode)

	with pytest.raises(OSError):
		build_release.build(str(root))
	assert (root / "bin" / "baton-tui").read_bytes() == before
	assert _staging_left_behind(root) == []


def test_products_built_from_different_cores_are_refused(root, monkeypatch):
	"""A build cannot hand the deployer a set it must refuse. This can only
	happen if the tree changes mid-build, which is exactly when a human wants
	to hear about it."""
	real = build_release.build_tui.build

	def different_core(target):
		manifest = real(target)
		manifest["embeds_core"] = dict(manifest["embeds_core"],
		                               package_sha256="ab" * 32)
		return manifest
	monkeypatch.setattr(build_release.build_tui, "build", different_core)

	with pytest.raises(build_release.BuildError, match="different cores"):
		build_release.build(str(root))
	assert not (root / "bin" / "baton").exists(), "a partial set was installed"


def test_products_disagreeing_on_the_protocol_are_refused(root, monkeypatch):
	real = build_release.build_tui.build

	def other_protocol(target):
		manifest = real(target)
		manifest["protocol_version"] = 11
		return manifest
	monkeypatch.setattr(build_release.build_tui, "build", other_protocol)

	with pytest.raises(build_release.BuildError, match="disagree on the protocol"):
		build_release.build(str(root))
	assert not (root / "bin" / "baton").exists()


def test_a_builder_producing_the_wrong_product_is_refused(root, monkeypatch):
	real = build_release.build_tui.build

	def mislabelled(target):
		return dict(real(target), tool="baton")
	monkeypatch.setattr(build_release.build_tui, "build", mislabelled)

	with pytest.raises(build_release.BuildError, match="not 'baton-tui'"):
		build_release.build(str(root))


# -- the recipe -------------------------------------------------------------

def test_the_justfile_has_one_release_build_recipe():
	"""One command, by ruling. The per-product builders stay as internal
	mechanisms, and the recipe says so."""
	justfile = (REPO / "justfile").read_text()
	recipes = [line.split(":")[0] for line in justfile.splitlines()
	           if line and not line[0].isspace() and line.rstrip().endswith(":")]
	assert "build" in recipes
	assert "build-tui" not in recipes, \
		"the console has no separate release-facing recipe any more"
	assert "tools/build_release.py" in justfile


def test_the_command_line_reports_what_it_installed(root):
	result = subprocess.run([sys.executable, str(TOOLS / "build_release.py"),
	                         str(root)], capture_output=True, text=True)
	assert result.returncode == 0, result.stderr
	reported = json.loads(result.stdout)
	assert reported["products"] == {"baton": "10.2.0", "baton-tui": "10.2.0"}
	assert "bin/baton" in reported["installed"]
	assert "bin/baton-tui" in reported["installed"]


def test_a_refusal_is_a_message_not_a_traceback(root, monkeypatch, tmp_path):
	"""The command a human runs. A traceback here reads as a broken tool
	rather than a tree that needs looking at."""
	script = tmp_path / "wrapper.py"
	script.write_text(
		"import sys\n"
		f"sys.path.insert(0, {str(TOOLS)!r})\n"
		"import build_release\n"
		"real = build_release.build_tui.build\n"
		"build_release.build_tui.build = lambda target: dict(\n"
		"    real(target), protocol_version=11)\n"
		"sys.argv = ['build_release', sys.argv[1]]\n"
		"exec(open(build_release.__file__).read().replace(\n"
		"    \"__name__ == \\\"__main__\\\"\", \"True\"))\n")
	result = subprocess.run([sys.executable, str(script), str(root)],
	                        capture_output=True, text=True)
	assert result.returncode == 1, result.stdout
	assert "Traceback" not in result.stderr, result.stderr
	assert result.stderr.startswith("build: "), result.stderr


def test_a_product_requiring_an_api_its_core_does_not_offer_is_refused(root,
                                                                       monkeypatch):
	"""R10. The check that decides whether a set can be RUN, and it was
	missing: this module claimed the build could not hand the deployer a set it
	must refuse, and a manifest requiring API 4 while embedding API 3 installed
	cleanly and was refused later, at publication. A claim a gate does not make
	is worse than no claim, because it stops anyone looking."""
	build_release.build(str(root))                      # an existing release
	marked = {}
	for relative in ("bin/baton", "bin/baton-tui",
	                 "dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json"):
		content = f"previous {relative}\n".encode()
		(root / relative).write_bytes(content)
		marked[relative] = content

	real = build_release.build_tui.build

	def outruns_its_core(target):
		# One PAST whatever the catalog currently offers: the number moves
		# with the core (3 -> 4 when the mailbox handshake landed), so a
		# hard-coded 4 stopped being "an API this core does not have" the day
		# the core reached 4.
		return dict(real(target),
		            requires_core_api=real(target)["embeds_core"]["api_version"] + 1)
	monkeypatch.setattr(build_release.build_tui, "build", outruns_its_core)

	with pytest.raises(build_release.BuildError, match="requires core API"):
		build_release.build(str(root))

	for relative, content in marked.items():
		assert (root / relative).read_bytes() == content, relative


def _record(candidate, **fields):
	"""Overwrite fields of a candidate's ownership record — for the refusal
	tests, the way nobody would."""
	path = pathlib.Path(candidate) / build_release.OWNERSHIP
	record = json.loads(path.read_text())
	record.update(fields)
	path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
	return path


def _restamp(candidate):
	"""Rewrite the ownership record to describe the tree as it stands now.

	What a build that had PRODUCED these bytes would have written. Fixtures
	that mark an old candidate to make it distinguishable need this: the record
	binds bytes now, so marked files without a matching record are a tampered
	candidate, which is a different test entirely.
	"""
	path = pathlib.Path(candidate) / build_release.OWNERSHIP
	path.unlink()
	build_release._stamp(str(candidate))
	return path


def _staging_left_behind(candidate) -> list:
	"""Anything this build created BESIDE the candidate and did not clean up.

	Staging lives here now rather than inside the candidate, so this is where a
	survivor would be.
	"""
	base = pathlib.Path(candidate).name
	return sorted(p.name for p in pathlib.Path(candidate).parent.iterdir()
	              if p.name.startswith(f".{base}-"))


def _classify(candidate, old: dict, new: dict) -> str:
	"""Is the visible candidate the complete old set, the complete new one, or
	a mixture? A mixture is the state the review caught and the one nothing
	downstream can detect, because every individual file is intact."""
	candidate = pathlib.Path(candidate)
	if not candidate.exists():
		return "absent"
	seen = {str(p.relative_to(candidate)): p.read_bytes()
	        for p in candidate.rglob("*") if p.is_file()}
	if seen == old:
		return "the complete previous candidate"
	if seen == new:
		return "the complete new candidate"
	return "A MIXTURE: " + ", ".join(
		sorted(name for name, content in seen.items()
		       if old.get(name) == content) or ["nothing recognisable"])


def _both_sets(root, tmp_path) -> tuple:
	"""The two states publication may leave behind, captured as bytes.

	The old candidate is MARKED because the build is deterministic: a rebuild
	produces identical bytes, so a half-published tree would be invisible and
	every assertion here would pass on exactly the failure being tested.
	"""
	build_release.build(str(root))
	for path in sorted(pathlib.Path(root).rglob("*")):
		# The ownership record is left alone: it is the previous candidate's
		# claim on its own directory, and rewriting it would be testing the
		# refusal path instead of publication.
		if path.is_file() and path.name != build_release.OWNERSHIP:
			path.write_bytes(f"previous {path.relative_to(root)}\n".encode())
	_restamp(root)                       # as the build that made these bytes would
	old = {str(p.relative_to(root)): p.read_bytes()
	       for p in pathlib.Path(root).rglob("*") if p.is_file()}

	reference = tmp_path / "reference"
	build_release.build(str(reference))
	new = {str(p.relative_to(reference)): p.read_bytes()
	       for p in reference.rglob("*") if p.is_file()}
	shutil.rmtree(reference)
	return old, new


def _rename_failing_at(call: int, monkeypatch):
	"""Fail the Nth rename of the publication phase, deterministically."""
	real = build_release.os.rename
	state = {"n": 0}

	def counted(source, target):
		state["n"] += 1
		if state["n"] == call:
			raise OSError(28, "No space left on device")
		return real(source, target)
	monkeypatch.setattr(build_release.os, "rename", counted)
	return state


# -- publication is a directory move, or it is nothing ----------------------
#
# R1. Preparation used to happen under `build/.release-*` and installation then
# replaced each payload leaf in the visible `build/`, one `os.replace` at a
# time. An injected failure at the fourth produced a candidate holding a new
# CLI beside an old console — every file intact, the set a mixture — at exactly
# the path `deploy` and the gates read. These tests fail the publication phase
# itself, which the previous suite never did.

def test_a_failure_retiring_the_old_candidate_leaves_it_whole(root, tmp_path,
                                                              monkeypatch):
	old, new = _both_sets(root, tmp_path)
	_rename_failing_at(1, monkeypatch)                  # the retirement itself

	with pytest.raises(OSError):
		build_release.build(str(root))

	assert _classify(root, old, new) == "the complete previous candidate"
	assert _staging_left_behind(root) == []


def test_a_failure_publishing_the_new_candidate_restores_the_old_one(root,
                                                                     tmp_path,
                                                                     monkeypatch):
	"""The window the old code could not survive: the moment between the two
	trees. The old candidate is put back, whole."""
	old, new = _both_sets(root, tmp_path)
	_rename_failing_at(2, monkeypatch)                  # staging -> build

	with pytest.raises(OSError):
		build_release.build(str(root))

	assert _classify(root, old, new) == "the complete previous candidate"
	assert _staging_left_behind(root) == []


def test_a_failure_publishing_a_first_candidate_leaves_nothing(tmp_path,
                                                               monkeypatch):
	"""With no previous candidate to restore, the visible state is ABSENCE —
	which is the trade taken deliberately. Absence fails closed: deploy and the
	gates say `run the build first`. A mixture does not."""
	candidate = tmp_path / "candidate"
	_rename_failing_at(1, monkeypatch)                  # the only rename there is

	with pytest.raises(OSError):
		build_release.build(str(candidate))

	assert not candidate.exists()
	assert _staging_left_behind(candidate) == []


@pytest.mark.parametrize("call", (1, 2))
def test_no_injected_publication_failure_produces_a_mixture(root, tmp_path,
                                                            monkeypatch, call):
	"""The review's own experiment, run as a gate: inject a failure at each
	step of publication and assert the visible state is never a mixture. The
	fourth `os.replace` of the old implementation would fail this."""
	old, new = _both_sets(root, tmp_path)
	_rename_failing_at(call, monkeypatch)

	with pytest.raises(OSError):
		build_release.build(str(root))

	assert _classify(root, old, new) in (
		"the complete previous candidate", "the complete new candidate", "absent")


def test_a_concurrent_reader_can_never_observe_a_mixture(root, tmp_path,
                                                          monkeypatch):
	"""What `deploy` could see if it ran DURING a build.

	The failure tests above look at the wreckage afterwards. This one looks at
	every intermediate state: the candidate is classified before and after each
	individual rename publication performs, which is exactly the set of moments
	another process could catch it in. The old per-leaf installation had one
	such moment per file, and all but the first and last were mixtures.
	"""
	old, new = _both_sets(root, tmp_path)
	observed = []

	def watching(real):
		def watched(source, target):
			observed.append(_classify(root, old, new))
			try:
				return real(source, target)
			finally:
				observed.append(_classify(root, old, new))
		return watched
	# BOTH primitives. Watching only `rename` would report "no rename at all"
	# against a per-leaf `replace` implementation -- a failure, but for the
	# wrong reason, and it would say nothing about what the reader SAW.
	monkeypatch.setattr(build_release.os, "rename", watching(build_release.os.rename))
	monkeypatch.setattr(build_release.os, "replace", watching(build_release.os.replace))

	build_release.build(str(root))

	assert observed, "publication performed no rename at all"
	assert set(observed) <= {"the complete previous candidate",
	                         "the complete new candidate", "absent"}, observed
	# ...and it really did pass through the absent state, which is the trade
	# this design takes rather than an accident nobody noticed.
	assert "absent" in observed, observed
	assert observed[-1] == "the complete new candidate", observed


def test_a_successful_build_publishes_the_complete_new_candidate(root, tmp_path):
	"""The other half of the same statement, so the classifier is not only ever
	shown failures."""
	old, new = _both_sets(root, tmp_path)
	build_release.build(str(root))
	assert _classify(root, old, new) == "the complete new candidate"


def test_the_candidate_never_certifies_as_a_mixture_because_it_never_is_one(
		root, tmp_path, monkeypatch):
	"""What the mixture actually cost: `deploy` reads this path. After an
	injected publication failure the deployer must still see a coherent set."""
	import deploy

	build_release.build(str(root))
	before = deploy.certified(str(root))["set_digest"]
	_rename_failing_at(2, monkeypatch)
	with pytest.raises(OSError):
		build_release.build(str(root))
	assert deploy.certified(str(root))["set_digest"] == before


def test_publication_replaces_the_tree_so_stale_files_do_not_survive(root):
	"""A growing list of leaves could never retire a file an earlier candidate
	left behind. Replacing the directory does it by construction.

	The stale files are added to the previous candidate's OWN record, which is
	what an earlier build that shipped them would have written. Files that
	appear in a candidate WITHOUT being recorded are a different thing
	entirely -- somebody put them there -- and publication refuses rather than
	deleting them.
	"""
	build_release.build(str(root))
	stale = root / "bin" / "baton-1.0.0-leftover"
	stale.write_bytes(b"from an earlier candidate\n")
	orphan = root / "docs" / "RELEASE-baton-0.9.0.md"
	orphan.write_bytes(b"# withdrawn\n")
	_restamp(root)                       # as the build that shipped them would

	build_release.build(str(root))

	assert not stale.exists(), "a stale artifact survived a rebuild"
	assert not orphan.exists(), "a withdrawn release note survived a rebuild"
	assert (root / "bin" / "baton").is_file()


def test_the_candidate_is_published_readable(root):
	"""`mkdtemp` makes a 0700 directory. Renaming it into place unchanged would
	publish a candidate nobody but its builder could enter — including the
	deploy step and every gate."""
	build_release.build(str(root))
	assert (root.stat().st_mode & 0o777) == 0o755
	assert ((root / "bin" / "baton").stat().st_mode & 0o111), "not executable"
	assert ((root / "dist" / "DISTRIBUTION.json").stat().st_mode & 0o777) == 0o644


def test_a_symlink_at_the_candidate_path_is_refused_not_retired(tmp_path):
	"""R11 restated for the new shape. Publication retires whatever is at the
	candidate path; if that is a link, retiring it would be disposing of
	somebody else's object, through a link, at a directory nobody named."""
	elsewhere = tmp_path / "somebody-elses-tree"
	elsewhere.mkdir()
	(elsewhere / "keep me").write_bytes(b"not part of any release\n")
	candidate = tmp_path / "candidate"
	candidate.symlink_to(elsewhere)

	with pytest.raises(build_release.BuildError, match="not a directory"):
		build_release.build(str(candidate))

	assert candidate.is_symlink(), "the link was consumed"
	assert (elsewhere / "keep me").read_bytes() == b"not part of any release\n"
	assert _staging_left_behind(candidate) == []


def test_a_link_inside_the_old_candidate_is_refused_not_walked(root, tmp_path):
	"""The old candidate is deleted wholesale, so a link that appeared inside
	it stops the deletion rather than being resolved by it. Nothing this build
	produced is a symlink; one that is there arrived by another route."""
	outside = tmp_path / "outside-secret"
	outside.write_bytes(b"not part of any release\n")
	build_release.build(str(root))
	planted = root / "bin" / "planted"
	planted.symlink_to(outside)

	with pytest.raises(build_release.BuildError, match="symlink"):
		build_release.build(str(root))

	assert outside.read_bytes() == b"not part of any release\n"
	assert planted.is_symlink(), "the link was consumed"
	assert (root / "bin" / "baton").is_file(), "the old candidate was disturbed"
	assert _staging_left_behind(root) == []


def test_nothing_beside_the_candidate_is_disturbed(root, tmp_path):
	"""Staging and retirement both happen in the candidate's parent. Neither
	may touch what else lives there."""
	neighbour = pathlib.Path(root).parent / "someone-elses-work"
	neighbour.mkdir()
	(neighbour / "notes.md").write_bytes(b"mine\n")
	hidden = pathlib.Path(root).parent / ".build-notes"
	hidden.write_bytes(b"also mine\n")

	build_release.build(str(root))

	assert (neighbour / "notes.md").read_bytes() == b"mine\n"
	assert hidden.read_bytes() == b"also mine\n"
	assert _staging_left_behind(root) == []


def test_an_uncertifiable_candidate_is_never_published(root, tmp_path,
                                                       monkeypatch):
	"""Certification runs against the staging tree, before publication. A
	candidate a human looks at is one that could actually be deployed."""
	import deploy

	old, new = _both_sets(root, tmp_path)

	def refuse(source):
		raise deploy.DeployError("the manifest pins a document that is not there")
	monkeypatch.setattr(deploy, "certified", refuse)

	with pytest.raises(build_release.BuildError, match="does not certify"):
		build_release.build(str(root))

	assert _classify(root, old, new) == "the complete previous candidate"
	assert _staging_left_behind(root) == []


# -- what publication is allowed to delete ---------------------------------
#
# R4. Publication retires whatever sits at the candidate path and then removes
# it RECURSIVELY. Refusing links and non-directories was not enough: an
# ordinary directory holding somebody's notes satisfied `isdir` and was
# deleted, while the module claimed the old candidate had been "resolved and
# checked". A check that cannot tell this build's output from a stranger's
# directory cannot authorize `rmtree`.

def _undisturbed(directory) -> dict:
	return {str(path.relative_to(directory)): path.read_bytes()
	        for path in sorted(pathlib.Path(directory).rglob("*")) if path.is_file()}


def test_an_ordinary_directory_at_the_candidate_path_is_refused(tmp_path):
	"""The reviewer's reproduction: a directory somebody keeps notes in."""
	occupied = tmp_path / "candidate"
	occupied.mkdir()
	(occupied / "unrelated-human-notes.txt").write_bytes(b"do not delete me\n")
	(occupied / "papers").mkdir()
	(occupied / "papers" / "draft.md").write_bytes(b"# still writing\n")
	before = _undisturbed(occupied)

	with pytest.raises(build_release.BuildError, match="carries no"):
		build_release.build(str(occupied))

	assert _undisturbed(occupied) == before, "an unrelated directory was disturbed"
	assert _staging_left_behind(occupied) == []


def test_an_empty_directory_at_the_candidate_path_is_accepted(tmp_path):
	"""`mkdir build` before the first build is an ordinary thing to do, and
	replacing an empty directory removes no bytes — which is the only thing
	this check exists to protect."""
	empty = tmp_path / "candidate"
	empty.mkdir()
	build_release.build(str(empty))
	assert (empty / "bin" / "baton").is_file()


@pytest.mark.parametrize("damage", [
	pytest.param({"raw": "{not json"}, id="not-json"),
	pytest.param({"raw": "[]"}, id="not-an-object"),
	pytest.param({"fields": {"format": "somebody.elses.marker"}}, id="wrong-format"),
	pytest.param({"fields": {"format_version": 99}}, id="unknown-version"),
	pytest.param({"fields": {"entries": ["bin/baton"]}}, id="entries-not-a-map"),
	pytest.param({"fields": {"entries": {}}}, id="entries-empty"),
	pytest.param({"fields": {"entries": {"bin/baton": "deadbeef"}}},
	             id="entry-not-described"),
	pytest.param({"fields": {"entries": {"bin/baton": {"mode": 493}}}},
	             id="entry-without-digest"),
	pytest.param({"fields": {"entries": {"bin/baton": {"sha256": "zz" * 32,
	                                                   "mode": 493}}}},
	             id="digest-not-hex"),
	pytest.param({"fields": {"entries": {"bin/baton": {"sha256": "ab" * 32}}}},
	             id="entry-without-mode"),
	pytest.param({"fields": {"entries": {"bin/baton": {"sha256": "ab" * 32,
	                                                   "mode": True}}}},
	             id="mode-not-an-integer"),
	pytest.param({"fields": {"entries": {"../../etc/passwd": {"sha256": "ab" * 32,
	                                                          "mode": 420}}}},
	             id="entry-escapes"),
	pytest.param({"fields": {"entries": {"/etc/passwd": {"sha256": "ab" * 32,
	                                                     "mode": 420}}}},
	             id="entry-absolute"),
])
def test_a_marked_but_malformed_record_is_refused(root, damage):
	"""A record is an authorization to delete a tree. Anything about it that
	this build did not write means the authorization is not this build's."""
	build_release.build(str(root))
	marker = root / "bin" / "something-a-human-put-here"
	marker.write_bytes(b"mine\n")
	if "raw" in damage:
		(root / build_release.OWNERSHIP).write_text(damage["raw"])
	else:
		_record(root, **damage["fields"])
	before = _undisturbed(root)

	with pytest.raises(build_release.BuildError):
		build_release.build(str(root))

	assert _undisturbed(root) == before, "a candidate was disturbed anyway"
	assert marker.read_bytes() == b"mine\n"
	assert _staging_left_behind(root) == []


def test_a_record_naming_one_path_twice_is_refused(root):
	"""`json.loads` keeps the LAST of a repeated key, so a record can carry a
	claim nothing ever checks.

	The duplicate here is built so that the surviving entry is the GENUINE one
	and every other check passes — otherwise the mismatch refuses first and
	the test proves nothing about duplicates. Which is exactly what the first
	version of it did.
	"""
	build_release.build(str(root))
	path = root / build_release.OWNERSHIP
	record = json.loads(path.read_text())
	repeated = "README.md"
	assert repeated in record["entries"]
	shadowed = json.dumps({"sha256": "a" * 64, "mode": 0o644})
	pairs = ", ".join(f"{json.dumps(name)}: {json.dumps(facts)}"
	                  for name, facts in record["entries"].items())
	path.write_text(
		'{"format": %s, "format_version": %d, "entries": {%s: %s, %s}}\n'
		% (json.dumps(record["format"]), record["format_version"],
		   json.dumps(repeated), shadowed, pairs))
	before = _undisturbed(root)

	with pytest.raises(build_release.BuildError, match="duplicate key"):
		build_release.build(str(root))

	assert _undisturbed(root) == before


def test_a_recorded_path_holding_a_special_file_is_refused(root):
	"""R6. The record used to bind NAMES. A FIFO at a recorded pathname is
	neither an extra name nor a missing one, so nothing could see it — and
	`rmtree` removed it and published a regular file over the top. Reading it
	would have hung the validator, which is why the leaf is opened
	`O_NONBLOCK` and its type confirmed on the descriptor."""
	build_release.build(str(root))
	recorded = root / "README.md"
	recorded.unlink()
	os.mkfifo(recorded)

	with pytest.raises(build_release.BuildError, match="not a regular file"):
		build_release.build(str(root))

	assert stat.S_ISFIFO(os.lstat(recorded).st_mode), "the FIFO was removed"
	assert (root / "bin" / "baton").is_file(), "the old candidate was disturbed"
	assert _staging_left_behind(root) == []


def test_changed_bytes_at_a_recorded_path_are_refused(root):
	"""The other half of R6: somebody's own text at a recorded pathname. The
	name matches, so only the digest can tell."""
	build_release.build(str(root))
	recorded = root / "README.md"
	recorded.write_bytes(b"# notes I was keeping in here\n")
	before = _undisturbed(root)

	with pytest.raises(build_release.BuildError, match="bytes have changed"):
		build_release.build(str(root))

	assert _undisturbed(root) == before
	assert recorded.read_bytes() == b"# notes I was keeping in here\n"


def test_a_changed_mode_at_a_recorded_path_is_refused(root):
	"""Mode is part of what a candidate IS: the executables are 0755 and
	everything else is 0644, set by the build rather than by whoever's umask
	happened to be in effect."""
	build_release.build(str(root))
	(root / "bin" / "baton").chmod(0o700)

	with pytest.raises(build_release.BuildError, match="is mode 700"):
		build_release.build(str(root))

	assert (root / "bin" / "baton").stat().st_mode & 0o777 == 0o700


def test_a_mutation_after_validation_does_not_reach_the_delete(root, tmp_path):
	"""THE RACE. The first validation answers about a public pathname anybody
	can write to; between that answer and `rmtree` there was a window in which
	a file could be added and swept into the recursive delete.

	The mutation is injected deterministically at the retirement rename, which
	is exactly that window."""
	old, new = _both_sets(root, tmp_path)
	real = build_release.os.rename
	planted = {}

	def mutating(source, target):
		result = real(source, target)
		if os.path.basename(target) == "candidate" and not planted:
			# Arrived in the holder, after the check at the public path.
			intruder = os.path.join(target, "docs", "slipped-in.md")
			with open(intruder, "wb") as writer:
				writer.write(b"# added between the check and the delete\n")
			planted["at"] = intruder
		return result
	monkeypatch = pytest.MonkeyPatch()
	monkeypatch.setattr(build_release.os, "rename", mutating)
	try:
		with pytest.raises(build_release.BuildError, match="no build put there"):
			build_release.build(str(root))
	finally:
		monkeypatch.undo()

	assert planted, "the mutation was never injected; this proves nothing"
	# The old candidate is back at its own pathname, with the intruder still
	# in it -- not deleted, and not published over.
	assert (root / "docs" / "slipped-in.md").read_bytes() == \
		b"# added between the check and the delete\n"
	assert (root / "bin" / "baton").read_bytes() == old["bin/baton"]
	assert _staging_left_behind(root) == []


def test_a_candidate_holding_a_file_nobody_recorded_is_refused(root):
	"""The case certification cannot answer: a valid set PLUS something else.
	`certified()` ignores files no manifest names, so it would bless this tree
	and the extra file would go into `rmtree` with it."""
	import deploy

	build_release.build(str(root))
	intruder = root / "docs" / "notes-i-was-keeping.md"
	intruder.write_bytes(b"# not from any build\n")
	assert deploy.certified(str(root))["set_digest"], \
		"certification is supposed to accept this tree; that is the point"
	before = _undisturbed(root)

	with pytest.raises(build_release.BuildError, match="which no build put there"):
		build_release.build(str(root))

	assert _undisturbed(root) == before
	assert intruder.read_bytes() == b"# not from any build\n"


def test_a_candidate_missing_something_it_recorded_is_refused(root):
	build_release.build(str(root))
	(root / "docs" / "EFFECTIVE-BATON.md").unlink()
	before = _undisturbed(root)

	with pytest.raises(build_release.BuildError, match="recorded but missing"):
		build_release.build(str(root))

	assert _undisturbed(root) == before


def test_a_symlinked_ownership_record_cannot_vouch_for_a_directory(tmp_path):
	"""The record is opened with `O_NOFOLLOW`, and this is the only test that
	can tell.

	The tree here is otherwise a PERFECT candidate — copied from a real build,
	contents matching the record entry for entry — so every other check
	passes and the sole thing standing between it and `rmtree` is that its
	record is a link rather than a file this build wrote. An earlier version
	of this test planted a link beside unrelated files, and it passed with
	`O_NOFOLLOW` removed: the mismatch refused it first, so the test proved
	nothing about following links.
	"""
	genuine = tmp_path / "genuine"
	build_release.build(str(genuine))

	occupied = tmp_path / "occupied"
	shutil.copytree(genuine, occupied)
	(occupied / build_release.OWNERSHIP).unlink()
	(occupied / build_release.OWNERSHIP).symlink_to(genuine / build_release.OWNERSHIP)
	before = _undisturbed(occupied)
	assert before, "the fixture is empty; this would prove nothing"

	with pytest.raises(build_release.BuildError, match="carries no|not a regular"):
		build_release.build(str(occupied))

	assert (occupied / build_release.OWNERSHIP).is_symlink(), "the link was consumed"
	assert _undisturbed(occupied) == before
	assert _staging_left_behind(occupied) == []


def test_a_recorded_entry_that_is_a_link_is_refused(root, tmp_path):
	"""Recorded by name, but the thing at that name is a link out of the tree.
	Deleting the tree must not be authorized by it."""
	outside = tmp_path / "outside"
	outside.write_bytes(b"not part of any release\n")
	build_release.build(str(root))
	replaced = root / "docs" / "EFFECTIVE-BATON.md"
	replaced.unlink()
	replaced.symlink_to(outside)

	with pytest.raises(build_release.BuildError, match="symlink"):
		build_release.build(str(root))

	assert outside.read_bytes() == b"not part of any release\n"
	assert replaced.is_symlink()


def test_a_valid_owned_candidate_is_retired_and_replaced(root, tmp_path):
	"""The positive case, so the refusals above are not the only behaviour
	anybody proves: an ordinary previous candidate is retired without ceremony
	and the new one takes its place."""
	old, new = _both_sets(root, tmp_path)
	assert (root / build_release.OWNERSHIP).is_file()

	result = build_release.build(str(root))

	assert _classify(root, old, new) == "the complete new candidate"
	assert set(result["products"]) == {"baton", "baton-tui"}
	assert _staging_left_behind(root) == []


def test_the_record_describes_the_candidate_it_ships_with(root):
	"""It is checked on the way IN as well as on the way out: a record that
	did not describe its own candidate would refuse the next build for a
	reason nobody could act on."""
	build_release.build(str(root))
	record = json.loads((root / build_release.OWNERSHIP).read_text())
	assert record["format"] == build_release.OWNERSHIP_FORMAT
	assert record["format_version"] == build_release.OWNERSHIP_FORMAT_VERSION
	present = {str(path.relative_to(root))
	           for path in root.rglob("*") if path.is_file()}
	assert set(record["entries"]) == present - {build_release.OWNERSHIP}
	build_release.build(str(root))          # and it authorizes the next build


# -- step two may not perform step one -------------------------------------
#
# R3. `tests/conftest.py` used to call `candidate.ensure()` before collection,
# which built the candidate when it was absent or looked stale. That collapsed
# the ruled sequence -- `just build`, `just test`, `just deploy` -- into one
# step: the suite was free to manufacture the very artifact it reports on, so a
# green run said nothing about the bytes a human was about to publish.

def _calls_the_builder(source: str) -> list:
	"""Every `…build(…)` call in a module, by the name it is written as.

	AST rather than substring matching: the first version of this test filtered
	lines mentioning `build_release`, which is precisely how the reinstated
	convenience is spelled, so the check passed on the regression it was
	written to catch. Reading the calls is the only form of this that means
	anything.
	"""
	import ast

	found = []
	for node in ast.walk(ast.parse(source)):
		if not isinstance(node, ast.Call):
			continue
		function = node.func
		name = (function.attr if isinstance(function, ast.Attribute)
		        else getattr(function, "id", None))
		if name in ("build", "ensure"):
			found.append(ast.unparse(function))
	return found


def test_the_session_hook_does_not_prepare_the_candidate():
	"""`tests/conftest.py` runs before collection, for every invocation. If it
	builds, `just test` is never a check of what `just build` produced."""
	import ast

	source = (REPO / "tests" / "conftest.py").read_text()
	assert _calls_the_builder(source) == [], "conftest builds something"
	# `pytest_configure` is permitted since bed522d: it registers the
	# `serial` marker for the split v11 runner and builds nothing — which is
	# what this test actually guards. Any OTHER hook is still a refusal,
	# because collection-time code is where build-on-demand crept in before.
	hooks = [node.name for node in ast.walk(ast.parse(source))
	         if isinstance(node, ast.FunctionDef) and node.name.startswith("pytest_")]
	assert hooks in ([], ["pytest_configure"]), \
		f"conftest runs {hooks} before collection"
	configure = [node for node in ast.walk(ast.parse(source))
	             if isinstance(node, ast.FunctionDef)
	             and node.name == "pytest_configure"]
	if configure:
		body_source = ast.get_source_segment(source, configure[0])
		assert _calls_the_builder(body_source) == []
		assert "addinivalue_line" in body_source, \
			"pytest_configure does something beyond registering markers"
	assert "candidate" not in source.split("# NOTHING HERE BUILDS")[0], \
		"conftest reaches for the candidate locator before collection again"


def test_the_locator_locates_and_does_not_build():
	"""The same rule one level down: moving the convenience out of conftest and
	into `candidate.ensure()` would be the same collapse, differently spelled."""
	import candidate as locator

	assert not hasattr(locator, "ensure"), "the build-on-demand entry point is back"
	assert _calls_the_builder(pathlib.Path(locator.__file__).read_text()) == [], \
		"the locator builds the candidate it claims to locate"


def test_the_test_recipe_runs_the_read_only_preflight():
	"""R5. Removing the implicit build left the recipe entering pytest with no
	check at all: candidate-dependent fixtures refuse only when their own tests
	execute, so a bare `just test` reported several errors part-way through a
	run rather than one instruction before it.

	The recipe asks the LOCATOR, not a second hand-written list of artifacts —
	the first version of this preflight checked two executables and would have
	passed a candidate with no manifests in it."""
	recipe = (REPO / "justfile").read_text().split("\ntest:")[1].split("\n\n")[0]
	assert "tests/candidate.py" in recipe, recipe
	assert "build/bin" not in recipe, \
		"the recipe keeps its own artifact list again"
	assert "build_release" not in recipe and "just build\"" not in recipe


def test_the_preflight_refuses_a_missing_candidate_and_builds_nothing(tmp_path,
                                                                      monkeypatch,
                                                                      capsys):
	import candidate as locator

	absent = tmp_path / "no-candidate"
	monkeypatch.setattr(locator, "ROOT", absent)
	monkeypatch.setattr(locator, "ARTIFACTS", (absent / "bin" / "baton",))

	assert locator.main([]) == 1
	assert "just build" in capsys.readouterr().err
	assert not absent.exists(), "the preflight built what it was asked to check"


def test_the_preflight_accepts_the_candidate_and_writes_nothing():
	import candidate as locator

	before = {str(path.relative_to(locator.ROOT)): path.stat().st_mtime_ns
	          for path in locator.ROOT.rglob("*") if path.is_file()}
	assert locator.main([]) == 0
	after = {str(path.relative_to(locator.ROOT)): path.stat().st_mtime_ns
	         for path in locator.ROOT.rglob("*") if path.is_file()}
	assert after == before, "the preflight touched the candidate"


@pytest.fixture
def preflight(tmp_path, monkeypatch):
	"""A copy of the real candidate, with the locator pointed at it.

	Copied rather than mutated in place: these tests damage a candidate in
	ways `just build` would refuse to publish, and the shared `build/` is what
	every other gate in the session is reading."""
	import candidate as locator

	copy = tmp_path / "candidate"
	shutil.copytree(locator.ROOT, copy)
	monkeypatch.setattr(locator, "ROOT", copy)
	monkeypatch.setattr(locator, "ARTIFACTS",
	                    tuple(copy / relative for relative in
	                          ("bin/baton", "bin/baton-tui",
	                           "dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json")))
	monkeypatch.setattr(locator, "CLI", copy / "bin" / "baton")
	monkeypatch.setattr(locator, "TUI", copy / "bin" / "baton-tui")
	monkeypatch.setattr(locator, "DIST", copy / "dist")
	return copy


def test_the_preflight_accepts_a_complete_candidate_unchanged(preflight):
	"""And touches nothing: byte hashes and metadata identical afterwards."""
	import candidate as locator

	def state():
		return {str(path.relative_to(preflight)):
		        (_digest(path), path.stat().st_mode, path.stat().st_mtime_ns)
		        for path in sorted(preflight.rglob("*")) if path.is_file()}

	before = state()
	assert locator.main([]) == 0
	assert state() == before


@pytest.mark.parametrize("damage", [
	"missing-payload", "missing-release-note", "missing-record",
	"tampered-record", "changed-leaf", "special-leaf", "extra-file",
	"manifest-mismatch",
])
def test_the_preflight_refuses_an_incomplete_or_unowned_candidate(preflight,
                                                                  capsys,
                                                                  damage):
	"""R7. The old preflight asked whether four pathnames existed: four
	placeholder files passed it while the payload, the release notes and the
	ownership record were all absent, and the public test run could then begin
	against a tree the deployer would refuse at the end of it."""
	import candidate as locator

	if damage == "missing-payload":
		(preflight / "README.md").unlink()
	elif damage == "missing-release-note":
		next(preflight.glob("docs/RELEASE-baton-*.md")).unlink()
	elif damage == "missing-record":
		(preflight / build_release.OWNERSHIP).unlink()
	elif damage == "tampered-record":
		_record(preflight, format_version=99)
	elif damage == "changed-leaf":
		(preflight / "README.md").write_bytes(b"# not what was built\n")
	elif damage == "special-leaf":
		(preflight / "README.md").unlink()
		os.mkfifo(preflight / "README.md")
	elif damage == "extra-file":
		(preflight / "docs" / "unexpected.md").write_bytes(b"# nobody built this\n")
	elif damage == "manifest-mismatch":
		# The record AGREES with the tree; the manifest does not. Only the
		# deployer's certification can see this one, which is why the preflight
		# runs it.
		(preflight / "bin" / "baton").write_bytes(b"#!/usr/bin/env python3\n")
		_restamp(preflight)

	assert locator.main([]) == 1
	captured = capsys.readouterr()
	assert captured.err.count("error:") == 1, captured.err
	assert "just build" in captured.err.lower(), captured.err
	assert captured.out == ""


def test_the_preflight_is_one_refusal_from_the_command_line(tmp_path):
	"""What `just test` actually runs, as a process, against a repository whose
	candidate is somewhere else entirely."""
	elsewhere = tmp_path / "no-candidate"
	probe = subprocess.run(
		[sys.executable, "-c",
		 "import sys; sys.path.insert(0, %r); import candidate, pathlib; "
		 "candidate.ROOT = pathlib.Path(%r); "
		 "candidate.ARTIFACTS = (candidate.ROOT / 'bin' / 'baton',); "
		 "sys.exit(candidate.main([]))" % (str(REPO / "tests"), str(elsewhere))],
		capture_output=True, text=True)
	assert probe.returncode == 1
	assert probe.stderr.count("error:") == 1, probe.stderr
	assert "just build" in probe.stderr
	assert "Traceback" not in probe.stderr, probe.stderr
	assert not elsewhere.exists()


def test_a_missing_candidate_is_a_refusal_that_names_the_skipped_step(tmp_path,
                                                                      monkeypatch):
	"""Fail CLEARLY, and build nothing. Absence is the state publication can
	leave behind, so this is the message a human meets after an interrupted
	build as well as after a forgotten one."""
	import candidate as locator

	absent = tmp_path / "no-candidate"
	monkeypatch.setattr(locator, "ROOT", absent)
	monkeypatch.setattr(locator, "ARTIFACTS", (absent / "bin" / "baton",
	                                           absent / "bin" / "baton-tui"))

	with pytest.raises(locator.MissingCandidate) as refusal:
		locator.require()

	assert "just build" in str(refusal.value)
	assert "bin/baton" in str(refusal.value)
	assert not absent.exists(), "the locator built what it was asked to find"


def test_the_locator_answers_with_the_candidate_when_it_is_there():
	import candidate as locator

	found = locator.require()
	assert found.root == pathlib.Path(build_release.CANDIDATE)
	assert found.cli.is_file() and found.tui.is_file()
	assert found.dist.is_dir()


def test_an_incomplete_candidate_is_missing_rather_than_usable(tmp_path,
                                                               monkeypatch):
	"""One absent artifact is enough. A manifest with no executable beside it
	describes a shape, not a release."""
	import candidate as locator

	root = tmp_path / "half"
	(root / "bin").mkdir(parents=True)
	(root / "bin" / "baton").write_bytes(b"#!/usr/bin/env python3\n")
	monkeypatch.setattr(locator, "ROOT", root)
	monkeypatch.setattr(locator, "ARTIFACTS", (root / "bin" / "baton",
	                                           root / "bin" / "baton-tui"))

	with pytest.raises(locator.MissingCandidate, match="baton-tui"):
		locator.require()


# -- the build may not touch what live consumers are running ---------------
#
# Installing a finished set over `bin/baton` and `bin/baton-tui` made every
# successful build a production cutover: teams run the repository executables
# and the shared event bridge names one by absolute path, so the bytes reached
# live consumers before `just deploy` could be the boundary it was written to
# be. The candidate is disposable and the checkout is not a build output.

def _checkout_state():
	import hashlib

	paths = sorted(list((REPO / "bin").glob("*")) + list((REPO / "dist").glob("*")))
	return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
	        for p in paths if p.is_file()}


def test_building_leaves_the_checkout_executables_untouched(tmp_path):
	"""Evidence 1 of the ruling: hash `bin/` and `dist/`, build, and prove
	every hash is unchanged while the candidate is refreshed."""
	before = _checkout_state()
	assert before, "the checkout has no artifacts to protect"

	candidate = tmp_path / "candidate"
	result = build_release.build(str(candidate))

	assert _checkout_state() == before, "a build changed the checkout"
	assert (candidate / "bin" / "baton").is_file()
	assert (candidate / "bin" / "baton-tui").is_file()
	assert set(result["products"]) == {"baton", "baton-tui"}


def test_building_into_the_checkout_is_refused():
	"""Not a default anyone can slip past: naming the repository is refused
	outright, because the refusal is the whole point of the ruling."""
	with pytest.raises(build_release.BuildError, match="refusing to build into"):
		build_release.build(str(REPO))
	assert build_release.CANDIDATE.endswith("/build")


def test_the_default_target_is_the_candidate(tmp_path, monkeypatch):
	"""The LIBRARY default follows `CANDIDATE`, and nothing else.

	SAID PRECISELY, because the earlier wording was not: this is not "the way
	`just build` calls it". The recipe runs `tools/build_release.py` with no
	command-line argument, and the script's `__main__` resolves `CANDIDATE`
	itself and passes it explicitly. What is tested here is the one step below
	that -- `build()` with no argument resolving the constant at call time --
	because that is what could silently drift to the checkout.

	`CANDIDATE` is redirected to a temporary root FIRST, and the guard test
	proves that ordering rather than trusting this docstring. The earlier
	version called `build()` bare against the real `build/`, so every `just
	test` run quietly rebuilt the shared candidate: the implicit build the
	ruled `just build` → `just test` → `just deploy` sequence exists to
	prevent, reintroduced by the test that checks the default."""
	elsewhere = tmp_path / "candidate"
	monkeypatch.setattr(build_release, "CANDIDATE", str(elsewhere))
	before = _checkout_state()
	candidate_before = _digest(pathlib.Path(REPO, "build", "bin", "baton"))

	result = build_release.build()          # no argument: the library default

	assert _checkout_state() == before, "the default target was the checkout"
	assert (elsewhere / "bin" / "baton").is_file(), \
		"the default target was not the candidate constant"
	assert set(result["products"]) == {"baton", "baton-tui"}
	assert _digest(pathlib.Path(REPO, "build", "bin", "baton")) == \
		candidate_before, "the suite rebuilt the shared candidate"


def test_the_candidate_is_a_complete_distribution_root(tmp_path):
	"""Evidence 4: everything a deployment needs, snapshotted at one moment
	from one tree — so `just test` and `just deploy` examine the same bytes."""
	import deploy

	candidate = tmp_path / "candidate"
	build_release.build(str(candidate))
	for relative in deploy.PAYLOAD:
		assert (candidate / relative).is_file(), relative
	for tool in ("baton", "baton-tui"):
		assert (candidate / "docs" / f"RELEASE-{tool}-10.2.0.md").is_file(), tool

	facts = deploy.certified(str(candidate))
	assert set(facts["products"]) == {"baton", "baton-tui"}


def test_a_template_edited_after_the_build_does_not_reach_the_deployment(tmp_path,
                                                                         monkeypatch):
	"""Evidence 3. The candidate is a SNAPSHOT: a Git-owned file edited between
	`just test` and `just deploy` cannot change what is deployed, because
	deployment reads payload bytes from the candidate and nowhere else."""
	import deploy

	source = tmp_path / "source"
	shutil.copytree(REPO / "docs", source / "docs")
	shutil.copytree(REPO / "examples", source / "examples")
	for name in ("README.md", "LICENSE"):
		shutil.copy2(REPO / name, source / name)
	monkeypatch.setattr(build_release, "ROOT", str(source))
	monkeypatch.setattr(build_release.build_zipapp, "ROOT", str(source))
	monkeypatch.setattr(build_release.build_tui, "ROOT", str(source))

	candidate = tmp_path / "candidate"
	build_release.build(str(candidate))
	snapshotted = (candidate / "README.md").read_bytes()

	# The maintained template moves on after the gate.
	(source / "README.md").write_bytes(b"# edited after the build\n")

	deploy.install(str(candidate), str(tmp_path / "dest"))
	installed = (tmp_path / "dest" / "app" / "baton-cli" / "v10" / "v10.2.0"
	             / "doc" / "README.md")
	assert installed.read_bytes() == snapshotted
	assert installed.read_bytes() != (source / "README.md").read_bytes()


def test_a_failed_payload_snapshot_exposes_no_candidate(tmp_path, monkeypatch):
	"""Evidence 2, second half: the products can build perfectly and the
	candidate still must not appear if its payload could not be taken."""
	candidate = tmp_path / "candidate"
	build_release.build(str(candidate))
	marked = (candidate / "README.md")
	marked.write_bytes(b"previous README\n")

	real = build_release.shutil.copyfile

	def fail_on_readme(source, target, *args, **kwargs):
		if str(target).endswith("README.md"):
			raise OSError(28, "No space left on device")
		return real(source, target, *args, **kwargs)
	monkeypatch.setattr(build_release.shutil, "copyfile", fail_on_readme)

	with pytest.raises(OSError):
		build_release.build(str(candidate))
	assert marked.read_bytes() == b"previous README\n"
	assert _staging_left_behind(candidate) == []


def test_a_missing_release_note_is_refused_at_build_time(tmp_path, monkeypatch):
	"""Where a human can still do something about it. Certification needs the
	note; discovering that at publication means the candidate was never
	deployable and the gate said nothing."""
	source = tmp_path / "source"
	shutil.copytree(REPO / "docs", source / "docs")
	shutil.copytree(REPO / "examples", source / "examples")
	for name in ("README.md", "LICENSE"):
		shutil.copy2(REPO / name, source / name)
	(source / "docs" / "RELEASE-baton-tui-10.2.0.md").unlink()
	monkeypatch.setattr(build_release, "ROOT", str(source))
	monkeypatch.setattr(build_release.build_zipapp, "ROOT", str(source))
	monkeypatch.setattr(build_release.build_tui, "ROOT", str(source))

	with pytest.raises(build_release.BuildError, match="no release note to ship"):
		build_release.build(str(tmp_path / "candidate"))


def test_deploy_defaults_to_the_candidate_and_says_so_when_it_is_absent(tmp_path):
	"""Evidence 5's precondition: `just deploy` publishes what `just build`
	prepared, and refuses legibly rather than falling back to the checkout."""
	import deploy

	assert deploy.CANDIDATE == build_release.CANDIDATE
	# The COMMAND's default, not just the constant: `just deploy DEST` passes
	# no `--source`, so this is what a human actually gets.
	parser_default = subprocess.run(
		[sys.executable, str(TOOLS / "deploy.py"), "publish", "--help"],
		capture_output=True, text=True)
	assert "build/" in parser_default.stdout, parser_default.stdout
	with pytest.raises(deploy.DeployError, match="run the build first"):
		deploy.install(str(tmp_path / "absent-candidate"), str(tmp_path / "dest"))


def test_no_test_can_target_the_shared_candidate():
	"""R30/R31/R32. The suite-wide property, checked suite-wide.

	Three versions of this have been wrong in three different ways, and each
	one looked right:

	  * a TEXT scan matched its own assertion string;
	  * signature and implementation checks pinned how `build()` resolves its
	    default and said nothing about what any test does with it;
	  * "the exempt function contains a redirect somewhere" passed for a
	    redirect written after the call, and for a second call before it.

	What it checks now, reading the syntax tree of every `tests/**/test_*.py`:
	no call to `build_release.build` may be bare or name `CANDIDATE` /
	`candidate.ROOT`, ANYWHERE -- including at module scope, which executes
	during collection and which the function-only walk never visited -- except
	for ONE call, in ONE file, in ONE function, preceded by exactly one
	redirect of `CANDIDATE`.

	The exemption is bound to the relative PATH as well as the name, so the
	same function name in another file is an offender rather than an
	inherited licence.
	"""
	import ast

	EXEMPT_FILE = "tests/packaging/test_release_build.py"
	EXEMPT_FUNCTION = "test_the_default_target_is_the_candidate"

	def targets_shared(call: ast.Call) -> bool:
		function = call.func
		if not (isinstance(function, ast.Attribute) and function.attr == "build"
		        and isinstance(function.value, ast.Name)
		        and function.value.id == "build_release"):
			return False
		if not call.args and not call.keywords:
			return True
		return any("CANDIDATE" in ast.unparse(argument)
		           or "candidate.ROOT" in ast.unparse(argument)
		           for argument in list(call.args)
		           + [keyword.value for keyword in call.keywords])

	offenders = []
	exempt_calls = []
	for path in sorted((REPO / "tests").rglob("test_*.py")):
		relative = str(path.relative_to(REPO))
		tree = ast.parse(path.read_text())
		# WHERE each call lives, including nowhere: a call at module scope runs
		# at import time, so it rebuilds the candidate during COLLECTION --
		# before any test has been selected, and invisibly to a walk that only
		# looks inside functions.
		enclosing = {}
		for node in ast.walk(tree):
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
				for inner in ast.walk(node):
					enclosing.setdefault(id(inner), node.name)
		for node in ast.walk(tree):
			if not isinstance(node, ast.Call) or not targets_shared(node):
				continue
			where = enclosing.get(id(node))
			if where is None:
				offenders.append(f"{relative}: module scope, line {node.lineno}")
			elif (relative, where) != (EXEMPT_FILE, EXEMPT_FUNCTION):
				offenders.append(f"{relative}::{where}")
			else:
				exempt_calls.append(node.lineno)
	assert offenders == [], \
		f"these target the shared candidate: {offenders}"

	# ...and the one exemption earns it by ORDER, not by vocabulary: exactly
	# one call, exactly one redirect, and the redirect first.
	assert len(exempt_calls) == 1, \
		f"{EXEMPT_FUNCTION} makes {len(exempt_calls)} shared-target calls"
	tree = ast.parse((REPO / EXEMPT_FILE).read_text())
	allowed = next(node for node in ast.walk(tree)
	               if isinstance(node, ast.FunctionDef)
	               and node.name == EXEMPT_FUNCTION)
	redirects = [call.lineno for call in ast.walk(allowed)
	             if isinstance(call, ast.Call)
	             and ast.unparse(call).startswith(
		             'monkeypatch.setattr(build_release, \'CANDIDATE\'')]
	assert len(redirects) == 1, \
		f"{EXEMPT_FUNCTION} redirects CANDIDATE {len(redirects)} times"
	assert redirects[0] < exempt_calls[0], \
		"the redirect does not precede the call it is supposed to qualify"


def test_the_builder_default_can_be_redirected():
	"""The other half, in the CODE: a default bound at definition cannot
	follow the constant, so no test could have redirected it even if it
	wanted to. That is why the suite-wide rule above was unenforceable
	before."""
	import inspect

	signature = inspect.signature(build_release.build)
	assert signature.parameters["root"].default is None
	source = pathlib.Path(inspect.getsourcefile(build_release)).read_text()
	assert "if root is None:\n\t\troot = CANDIDATE" in source