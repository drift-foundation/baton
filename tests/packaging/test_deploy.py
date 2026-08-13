"""Publishing a certified release outside the repository.

A checkout is a workspace; it changes under people who are not watching it.
These pin the rules that make a deployed tree worth pointing at: the human
names the version, nothing partial ever appears at the destination, a version
directory is never replaced, and every file the manifests address is certified
before a byte is written.

The source tree used here is a CONSTRUCTED release, not the repository. The
repository is currently not a coherent 1.0.0 release — its protocol document
has moved on from the hash the frozen manifest pins — and that is exactly the
mixed-version state publish must refuse, so it cannot also be the fixture that
proves publish works.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
DEPLOY = REPO / "tools" / "deploy.py"

sys.path.insert(0, str(REPO / "tools"))


CORE_DIGEST = "c0" * 32


def run(*args):
	return subprocess.run([sys.executable, str(DEPLOY), *args], capture_output=True)


def _sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


@pytest.fixture(autouse=True)
def _restore_modes(tmp_path):
	"""Let pytest clean up after a test that hardened a tree.

	A deployed tree is `0555` by design, which is exactly what stops accidental
	writes -- and also what stops `rm_rf` from removing the temporary
	directory afterwards. Restoring the write bit at teardown keeps the
	hardening honest in the product and tidy in the suite."""
	yield
	for current, directories, _files in os.walk(tmp_path, topdown=False):
		for name in directories:
			try:
				os.chmod(os.path.join(current, name), 0o700)
			except OSError:
				pass
		try:
			os.chmod(current, 0o700)
		except OSError:
			pass


# A NUMERIC GENERATION, deliberately. From v11 onward a release's major IS the
# protocol generation it serves, so a fixture at protocol 10 with majors of 1
# describes a pair that can no longer be installed anywhere except the frozen
# legacy exception. Generation 11 keeps what this fixture was always for --
# two products at DIFFERENT versions in one certified set -- and makes it the
# shape the deployer must accept. The CORE stays 1.1.0: core versioning is
# independent of both, which is the whole point of the catalog.
# The synthetic candidate lives in `synthetic.py` because both deployment
# suites need it: this one to make exactly one thing wrong, the layout one to
# install two genuinely different releases.
from synthetic import CATALOG, _zipapp, _core_digest, candidate_tree, rebuild  # noqa: E402,F401


@pytest.fixture
def release(tmp_path):
	return candidate_tree(tmp_path)


def deploy_digest(source) -> str:
	"""The certified candidate's set digest — provenance now, not a pathname."""
	import deploy
	return deploy.certified(str(source))["set_digest"]


def release_dir(destination, source, tool="baton"):
	"""Where installing `source` puts one product: its generation directory and
	its exact version, both DERIVED — the path is a claim about the bytes, and
	`verify-release` is what stops that claim from lying."""
	import deploy

	facts = deploy.certified(str(source))
	manifest = facts["manifests"][
		"dist/DISTRIBUTION.json" if tool == "baton" else "dist/DISTRIBUTION-TUI.json"]
	namespace = deploy.namespace_for(tool, manifest["product_version"],
	                                 facts["protocol_version"])
	return (pathlib.Path(destination) / "app" / deploy.PRODUCT_DIRS[tool]
	        / namespace / ("v" + manifest["product_version"]))


def installed_anything(destination) -> list:
	"""Every exact release directory under a destination, however deep."""
	app = pathlib.Path(destination) / "app"
	if not app.is_dir():
		return []
	return sorted(str(p.relative_to(app)) for p in app.glob("*/*/v*"))


def _publish_set(source, destination):
	"""Build a SUPERSEDED `set-<digest>/` directory, in the test rather than in
	the tool.

	The set layout is no longer how anything is deployed — exact per-product
	releases replaced it — but published sets exist on disk and `verify` still
	reads them. The reader stays covered; the writer is gone, so this fixture
	is what produces its input."""
	import deploy

	facts = deploy.certified(str(source))
	version_dir = pathlib.Path(destination) / ("set-" + facts["set_digest"])
	files = {}
	for name in facts["payload"]:
		data = (pathlib.Path(source) / name).read_bytes()
		target = version_dir / name
		target.parent.mkdir(parents=True, exist_ok=True)
		target.write_bytes(data)
		files[name] = _sha(data)
	record = {"record_version": 2, "set_digest": facts["set_digest"],
	          "protocol_version": facts["protocol_version"],
	          "manifests": facts["manifests"], "products": facts["products"],
	          "files": dict(sorted(files.items()))}
	(version_dir / "DEPLOYMENT.json").write_text(
		json.dumps(record, indent=2, sort_keys=True) + "\n")
	for path in sorted(version_dir.rglob("*"), reverse=True):
		path.chmod(0o555 if path.is_dir() or path.parent.name == "bin" else 0o444)
	version_dir.chmod(0o555)
	return version_dir


@pytest.fixture
def deployed(release, tmp_path):
	"""A destination with both products installed as exact releases."""
	dest = tmp_path / "deploy"
	done = run("publish", str(dest), "--source", str(release))
	assert done.returncode == 0, done.stderr
	return dest, release_dir(dest, release)


@pytest.fixture
def published_set(release, tmp_path):
	"""A destination holding a set published under the superseded layout."""
	dest = tmp_path / "sets"
	dest.mkdir()
	return dest, _publish_set(release, dest)


# -- the ruled command and payload ----------------------------------------

def test_each_product_is_installed_as_its_own_exact_release(release, tmp_path):
	"""SUPERSEDED TWICE, and the property survived both times.

	First the operator named the release and publish refused unless both
	manifests said exactly it -- impossible once two products version
	independently. Then the set digest named the whole set -- exact, and
	unreadable. What survives is that an operator gets ONE specific thing
	rather than "whatever the manifests happen to hold": now it is an exact
	release path per product, and the digest remains as provenance tying them
	to one certified candidate.
	"""
	dest = tmp_path / "dest"
	done = run("publish", str(dest), "--source", str(release))
	assert done.returncode == 0, done.stderr

	cli = release_dir(dest, release, "baton")
	tui = release_dir(dest, release, "baton-tui")
	assert cli.is_dir() and tui.is_dir()
	assert cli.parent.name == "v11" and tui.parent.name == "v11"
	assert cli.name == "v11.1.0" and tui.name == "v11.4.0"
	assert (cli / "bin" / "baton").is_file()
	assert (tui / "bin" / "baton-tui").is_file()

	printed = json.loads(done.stdout)
	assert printed["set_digest"] == deploy_digest(release)
	assert {r["tool"]: r["version"] for r in printed["releases"]} == \
		{"baton": "11.1.0", "baton-tui": "11.4.0"}
	assert {r["state"] for r in printed["releases"]} == {"installed"}
	# The exact path to RUN is printed beside each alias, so nothing has to
	# derive it and nothing is tempted to configure the alias itself.
	assert sorted(a["execute"] for a in printed["aliases"]) == sorted(
		[str(cli / "bin" / "baton"), str(tui / "bin" / "baton-tui")])

	# A malformed product version in a manifest is refused before anything is
	# written -- the semantic spelling is still ruled.
	broken = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	broken["product_version"] = "v1.1"
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(broken))
	malformed = run("publish", str(tmp_path / "other"), "--source", str(release))
	assert malformed.returncode != 0
	assert b"major.minor.patch" in malformed.stderr


def test_the_release_document_follows_each_product(release, tmp_path):
	"""Hardcoding `RELEASE-1.0.0.md` would ship the previous announcement, or
	fail once it was retired. Each product now carries its OWN announcement in
	its own release, so the console's note cannot travel with the CLI."""
	dest = tmp_path / "dest"
	assert run("publish", str(dest), "--source", str(release)).returncode == 0
	cli = release_dir(dest, release, "baton")
	tui = release_dir(dest, release, "baton-tui")
	assert (cli / "doc" / "RELEASE-baton-11.1.0.md").exists()
	assert (tui / "doc" / "RELEASE-baton-tui-11.4.0.md").exists()
	assert not (cli / "doc" / "RELEASE-baton-tui-11.4.0.md").exists()
	assert not (tui / "doc" / "RELEASE-baton-11.1.0.md").exists()

	(release / "docs" / "RELEASE-baton-tui-11.4.0.md").unlink()
	missing = run("publish", str(tmp_path / "other"), "--source", str(release))
	assert missing.returncode != 0
	assert b"RELEASE-baton-tui-11.4.0.md is missing" in missing.stderr


def test_the_example_config_ships_and_stays_inert(deployed, release, tmp_path):
	"""Ruled: the template ships. It is a config SHAPE to copy — and publish
	proves it names no live authority, because a config inside a deployment is
	a config someone will point at."""
	dest, version_dir = deployed
	shipped = version_dir / "conf" / "baton.json.example"
	assert shipped.exists()
	document = json.loads(shipped.read_text())
	assert "participants" in document
	assert document["roots"] == {}

	# No authority, and nothing that looks like one, anywhere in the tree.
	assert list(dest.rglob("*.sqlite3")) == []
	# The template ships under `conf/` with a name nobody can mistake for a
	# live config: `conf/` holds shipped defaults, never configuration.
	assert [p for p in dest.rglob("baton.json")] == []

	# A template naming a real authority is refused.
	live = tmp_path / "live-root"
	live.mkdir()
	(release / "examples" / "baton.json").write_text(json.dumps({
		"config_version": 1, "protocol_version": 11, "generation": 1,
		"mailbox": {"name": "x"}, "participants": {},
		"roots": {"src": str(live)}, "retention_days": 90}))
	refused = run("publish", str(tmp_path / "other"), "--source", str(release))
	assert refused.returncode != 0
	assert b"points at an existing absolute root" in refused.stderr


# -- certification ----------------------------------------------------------

def test_a_manifest_pinned_protocol_document_is_certified(release, tmp_path):
	"""R2. Only the artifacts were checked, so 1.0 binaries could be paired
	with newer protocol prose and blessed by a record written over the
	mixture — whose own later `verify` would then pass."""
	(release / "docs" / "AGENTS-MAILBOX-PROTO.md").write_bytes(b"# moved on\n")
	dest = tmp_path / "dest"
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"does not match the hash pinned" in refused.stderr
	assert installed_anything(dest) == [], \
		"a refused publish left a release behind"


def test_the_manifests_must_agree_on_the_protocol(release, tmp_path):
	catalog = json.loads(json.dumps(CATALOG))
	catalog["protocol_version"] = 12
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"disagree on the protocol version" in refused.stderr


def test_publishing_refuses_an_uncertified_artifact(release, tmp_path):
	artifact = release / "bin" / "baton"
	artifact.write_bytes(artifact.read_bytes() + b"\n# not the certified bytes\n")
	dest = tmp_path / "dest"
	out = run("publish", str(dest), "--source", str(release))
	assert out.returncode != 0
	assert b"not certified" in out.stderr
	assert not dest.exists() or list(dest.iterdir()) == []


# -- nothing partial ever appears ------------------------------------------

def test_a_missing_late_payload_file_leaves_no_version_behind(release, tmp_path):
	"""R3, reproduced: the old tool filled the final directory as it copied,
	so a missing LICENSE left a partial set directory that the immutability rule
	then blocked anyone from repairing."""
	(release / "LICENSE").unlink()
	dest = tmp_path / "dest"
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"LICENSE is missing" in refused.stderr
	assert installed_anything(dest) == [], "a partial release was published"


def test_a_copy_failure_midway_leaves_no_version_and_no_staging(release, tmp_path,
                                                                monkeypatch):
	"""The same guarantee when the failure is not a missing file: an interrupt
	or a write error midway must leave the destination exactly as it was."""
	import deploy

	real_open = deploy._open_regular
	state = {"seen": 0}

	def explode(path):
		state["seen"] += 1
		if state["seen"] > 6:
			raise OSError("disk gave up")
		return real_open(path)

	monkeypatch.setattr(deploy, "_open_regular", explode)
	dest = tmp_path / "dest"
	with pytest.raises(OSError):
		deploy.install(str(release), str(dest))

	assert installed_anything(dest) == [], "a partial release survived"
	leftovers = [str(p) for p in dest.rglob(".staging-*")] if dest.exists() else []
	assert leftovers == [], f"staging left behind: {leftovers}"


def test_an_existing_empty_release_directory_is_never_replaced(release, tmp_path):
	"""`rename` would happily consume an empty directory. A release somebody
	else created, however empty, is not this tool's to overwrite -- and an
	empty one cannot verify, so it is refused rather than filled in."""
	dest = tmp_path / "dest"
	release_dir(dest, release).mkdir(parents=True)
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"does not verify" in refused.stderr
	assert list(release_dir(dest, release).iterdir()) == [], \
		"the empty directory was written into"


def test_reinstalling_the_same_candidate_is_idempotent(deployed, release):
	"""Publishing the same certified candidate twice must be SAFE, not an
	error: the ruling is that an identical exact release reports
	`already_installed` and is not rewritten. What is refused is a DIFFERENT
	set of bytes claiming to be the same version."""
	dest, version_dir = deployed
	# EXCEPT the operations record, which is append-only evidence about ACTS:
	# a second deployment is a second act and says so, while the releases it
	# reports on are untouched.
	before = {str(p.relative_to(dest)): p.read_bytes()
	          for p in dest.rglob("*") if p.is_file()
	          and "operations/" not in str(p.relative_to(dest))}

	again = run("publish", str(dest), "--source", str(release))
	assert again.returncode == 0, again.stderr
	printed = json.loads(again.stdout)
	assert {r["state"] for r in printed["releases"]} == {"already_installed"}
	assert {str(p.relative_to(dest)): p.read_bytes()
	        for p in dest.rglob("*") if p.is_file()
	        and "operations/" not in str(p.relative_to(dest))} == before
	assert len(list((dest / "operations").glob("*.json"))) == 2

	# Different bytes under the same version are a different thing entirely.
	source = pathlib.Path(str(release))
	(source / "README.md").write_bytes(b"# a different readme\n")
	rebuild(source, "DISTRIBUTION.json", "baton")
	rebuild(source, "DISTRIBUTION-TUI.json", "baton-tui")
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"describes a DIFFERENT" in refused.stderr
	assert (version_dir / "doc" / "README.md").read_bytes() == b"# baton\n"


def test_a_directory_appearing_at_the_rename_boundary_is_not_replaced(release,
                                                                     tmp_path,
                                                                     monkeypatch):
	"""R1. A `lexists` check followed by `os.rename` is cooperative at best:
	any process can create the final path in between, and POSIX rename then
	consumes an empty directory and reports success over an object this tool
	did not create.

	The race is inserted exactly there — between the check and the
	publication — which a cooperative lock cannot close and
	`RENAME_NOREPLACE` can."""
	import deploy

	dest = tmp_path / "dest"
	real = deploy._rename_noreplace

	def race(source, target):
		os.makedirs(target, exist_ok=True)       # somebody else, just now
		return real(source, target)

	monkeypatch.setattr(deploy, "_rename_noreplace", race)
	with pytest.raises(deploy.DeployError) as refused:
		deploy.install(str(release), str(dest))
	assert "never rewritten in place" in str(refused.value)
	assert list(release_dir(dest, release, "baton-tui").iterdir()) == [], \
		"the directory was written into"
	assert not list(dest.rglob(".staging-*")), "staging survived the refusal"


def test_publication_refuses_when_it_cannot_be_atomic(release, tmp_path,
                                                      monkeypatch):
	"""Fail closed. Degrading to a replacing rename would reintroduce the
	defect behind a successful exit code."""
	import ctypes
	import deploy

	class Unsupported:
		def __getattr__(self, name):
			raise AttributeError(name)

		def syscall(self, *args):
			ctypes.set_errno(errno.ENOSYS)
			return -1

	monkeypatch.setattr(ctypes, "CDLL", lambda *a, **k: Unsupported())
	dest = tmp_path / "dest"
	with pytest.raises(deploy.DeployError) as refused:
		deploy.install(str(release), str(dest))
	assert "atomic no-replace" in str(refused.value)
	assert installed_anything(dest) == []
	assert not list(dest.rglob(".staging-*"))


def test_a_failure_after_hardening_still_removes_only_its_own_staging(release,
                                                                     tmp_path,
                                                                     monkeypatch):
	"""R2. `_harden` makes every staging directory `0555`, so an ordinary
	`rmtree` could not unlink anything inside them: a failure at the final
	rename left the whole hardened tree behind. The earlier copy-failure test
	failed BEFORE hardening and never reached this path."""
	import deploy

	dest = tmp_path / "dest"
	generation = release_dir(dest, release, "baton-tui").parent
	generation.mkdir(parents=True)
	unrelated = generation / ".staging-baton-tui-99999"
	unrelated.mkdir()
	(unrelated / "someone-elses-work").write_text("do not delete me\n")

	def explode(source, target):
		raise OSError("the rename failed after hardening")

	monkeypatch.setattr(deploy, "_rename_noreplace", explode)
	with pytest.raises(OSError):
		deploy.install(str(release), str(dest))

	assert (unrelated / "someone-elses-work").exists(), \
		"an unrelated staging directory was deleted"
	mine = [p for p in dest.rglob(".staging-*") if p != unrelated]
	assert mine == [], f"the hardened staging tree survived: {mine}"


def test_every_nested_directory_is_fsynced_before_publication(release, tmp_path,
                                                              monkeypatch):
	"""R4. Only the staging ROOT was synced, so `bin`, `docs`, `dist` and
	`examples` entries were not durable — and the mode changes happened after
	the file fsyncs, so those were not either."""
	import deploy

	synced = []
	real_fsync = os.fsync

	def record(fd):
		try:
			synced.append(os.path.realpath(f"/proc/self/fd/{fd}"))
		except OSError:
			pass
		return real_fsync(fd)

	monkeypatch.setattr(os, "fsync", record)
	dest = tmp_path / "dest"
	deploy.install(str(release), str(dest))

	staged = [p for p in synced if ".staging-baton" in p]
	for nested in ("bin", "doc", "conf"):
		assert any(p.endswith("/" + nested) for p in staged), \
			f"{nested} was never fsynced: {staged}"
	# And the generation directory, which is where the release and its alias
	# both appear.
	assert any(p.rstrip("/").endswith("/v11") for p in synced), \
		"the generation directory was not fsynced"


# -- what a deployed tree is ------------------------------------------------

def test_a_deployed_tree_is_read_only_and_runnable(deployed):
	"""R4. The progress record claimed read-only and the modes said 0775.

	This is not tamper-proofing: whoever owns the filesystem can change a mode
	and edit anything, which is what `verify` answers. It stops accident."""
	_dest, version_dir = deployed
	for path in version_dir.rglob("*"):
		mode = stat.S_IMODE(path.lstat().st_mode)
		assert not mode & stat.S_IWUSR, f"{path} is writable: {oct(mode)}"
		assert not mode & (stat.S_IWGRP | stat.S_IWOTH), f"{path} is {oct(mode)}"
		if path.is_dir() or path.parent.name == "bin":
			assert mode & stat.S_IXUSR, f"{path} is not usable: {oct(mode)}"


def test_verification_detects_tampering_extra_files_and_symlinks(published_set, tmp_path):
	_dest, version_dir = published_set
	assert run("verify", str(version_dir)).returncode == 0

	readme = version_dir / "README.md"
	readme.chmod(0o644)
	readme.write_text(readme.read_text() + "tampered\n")
	bad = run("verify", str(version_dir))
	assert bad.returncode != 0 and b"README.md" in bad.stdout

	# A file nobody recorded is as much a problem as a changed one. The root
	# has to be writable to add one, so that mode change is reported too --
	# which is itself the point of checking modes.
	version_dir.chmod(0o755)
	(version_dir / "EXTRA.txt").write_text("who put this here\n")
	extra = run("verify", str(version_dir))
	assert extra.returncode != 0
	assert b"expected mode 555" in extra.stdout
	version_dir.chmod(0o555)
	extra = run("verify", str(version_dir))
	assert extra.returncode != 0 and b"present but not recorded" in extra.stdout
	version_dir.chmod(0o755)
	(version_dir / "EXTRA.txt").unlink()
	version_dir.chmod(0o555)

	# And a recorded path REPLACED by a symlink to identical bytes is refused:
	# following it would let a deployed tree describe bytes living elsewhere.
	elsewhere = tmp_path / "elsewhere.md"
	elsewhere.write_bytes(readme.read_bytes())
	# The deployed directory is 0555, so replacing an entry needs the write bit
	# back — which is the hardening doing its job on the way to this test's
	# actual subject.
	version_dir.chmod(0o755)
	readme.unlink()
	readme.symlink_to(elsewhere)
	version_dir.chmod(0o555)
	linked = run("verify", str(version_dir))
	assert linked.returncode != 0 and b"symlink" in linked.stdout


def test_a_symlinked_payload_entry_is_refused_at_publish(release, tmp_path):
	target = tmp_path / "outside.md"
	target.write_bytes(b"# baton\n")
	(release / "README.md").unlink()
	(release / "README.md").symlink_to(target)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"symlink" in refused.stderr


def test_the_product_record_is_reproducible(release, tmp_path):
	"""No timestamps inside a release, so two people installing one candidate
	get identical trees and verification can be exact."""
	records = []
	for name in ("a", "b"):
		dest = tmp_path / name
		assert run("publish", str(dest), "--source", str(release)).returncode == 0
		records.append((release_dir(dest, release) / "PRODUCT.json").read_bytes())
	assert records[0] == records[1]
	record = json.loads(records[0])
	assert record["format_version"] == 1
	assert record["tool"] == "baton"
	assert record["product_version"] == "11.1.0"
	assert record["protocol_version"] == 11
	assert record["namespace"] == "v11"
	# THE DIGEST SURVIVES AS PROVENANCE. It no longer names the path a human
	# types, and it is still the cheapest possible answer to "did these two
	# products come out of one certified candidate".
	assert record["provenance"]["set_digest"] == deploy_digest(release)
	assert "legacy_mapping" not in record, \
		"a numeric generation needs no exception"


def test_a_major_one_release_at_protocol_ten_now_has_nowhere_to_live(release,
                                                                     tmp_path):
	"""SUPERSEDED 2026-08-13. This used to install `baton` 1.1.0 at protocol 10
	into a granted `legacy` namespace and assert the record explained the
	exception out loud.

	The grant is gone. The frozen 1.x pair is a hand-maintained directory that
	the deployer neither installs nor describes, so the exact shape this test
	used to certify is now the shape it must REFUSE -- and refuse before
	writing anything, because a half-installed pair in a namespace that does
	not exist is worse than a refusal."""
	catalog = json.loads(json.dumps(CATALOG))
	catalog["protocol_version"] = 10
	catalog["products"]["baton"]["version"] = "1.1.0"
	catalog["products"]["baton-tui"]["version"] = "1.1.0"
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	for tool in ("baton", "baton-tui"):
		(release / "docs" / f"RELEASE-{tool}-1.1.0.md").write_bytes(b"# note\n")
	example = json.loads((release / "examples" / "baton.json").read_text())
	example["protocol_version"] = 10
	(release / "examples" / "baton.json").write_text(json.dumps(example))

	dest = tmp_path / "dest"
	outcome = run("publish", str(dest), "--source", str(release))
	assert outcome.returncode != 0
	assert b"does not equal its generation" in outcome.stdout + outcome.stderr
	assert not (dest / "app").exists(), "it wrote before it refused"


def test_a_version_whose_major_is_not_its_generation_is_refused(release,
                                                                tmp_path):
	"""Everything except the frozen pair. A release claiming protocol 11 with
	major 3 has nowhere to live: `v11` would be a lie and `v3` would not serve
	the mailbox it claims."""
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton"]["version"] = "3.0.0"
	# BOTH products from the one changed catalog: rebuilding a single artifact
	# would embed two different cores and the set would be refused for that
	# instead, which is a different test.
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	(release / "docs" / "RELEASE-baton-3.0.0.md").write_bytes(b"# note\n")

	dest = tmp_path / "dest"
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"does not equal its generation" in refused.stderr
	assert installed_anything(dest) == []


# -- discovery aliases ------------------------------------------------------
#
# SUPERSEDES activation. There is no global `current` naming one set for both
# products: each generation directory carries a `latest` symlink, they advance
# independently, and NOTHING executes through them -- a consumer resolves the
# alias once and runs the exact release path.

def test_the_alias_is_relative_verified_and_atomic(deployed, release, tmp_path):
	dest, version_dir = deployed
	generation = version_dir.parent
	alias = generation / "latest"
	assert alias.is_symlink() and os.readlink(alias) == version_dir.name
	assert not os.path.isabs(os.readlink(alias)), \
		"an absolute link breaks if the root is moved or mounted elsewhere"
	assert (alias / "bin" / "baton").exists()
	assert not list(generation.glob(".latest-*")), "a staging link survived"

	# A release that no longer verifies cannot be aliased, and the refusal
	# leaves the pointer exactly where it was.
	readme = version_dir / "doc" / "README.md"
	version_dir.chmod(0o755)
	(version_dir / "doc").chmod(0o755)
	readme.chmod(0o644)
	readme.write_text("tampered\n")
	refused = run("alias", str(generation), version_dir.name)
	assert refused.returncode != 0 and b"does not verify" in refused.stderr
	assert os.readlink(alias) == version_dir.name, \
		"a refusal disturbed the pointer"


def test_an_alias_never_leaves_its_generation(deployed, release, tmp_path):
	"""Absolute, dotted, cross-generation, non-exact and missing targets: each
	refused with the old alias untouched."""
	dest, version_dir = deployed
	generation = version_dir.parent
	alias = generation / "latest"
	before = os.readlink(alias)

	for target in (str(version_dir), "../v11/v11.1.0", "./v11.1.0", "latest",
	               "v11.9.9", "v1.1", ".hidden", "v11.1.0/bin"):
		refused = run("alias", str(generation), target)
		assert refused.returncode != 0, target
		assert os.readlink(alias) == before, f"{target} moved the alias"


def test_an_alias_that_is_not_a_symlink_is_never_replaced(deployed):
	"""A shipped command must not delete an object it did not create."""
	dest, version_dir = deployed
	generation = version_dir.parent
	alias = generation / "latest"
	alias.unlink()
	alias.write_text("somebody's notes\n")

	refused = run("alias", str(generation), version_dir.name)
	assert refused.returncode != 0
	assert b"not a symlink" in refused.stderr
	assert alias.read_text() == "somebody's notes\n"


def test_rollback_is_the_same_call_naming_the_previous_release(release,
                                                              tmp_path):
	"""The old exact release stays installed, so going back is another
	validated alias replacement rather than a restore."""
	dest = tmp_path / "dest"
	assert run("publish", str(dest), "--source", str(release)).returncode == 0
	first = release_dir(dest, release)
	generation = first.parent

	# BOTH products move: they are built from one catalog, so a catalog change
	# changes both artifacts. Leaving the console at 11.4.0 would mean its
	# unchanged exact release now holds different bytes -- refused, correctly,
	# and a different test.
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton"]["version"] = "11.2.0"
	catalog["products"]["baton-tui"]["version"] = "11.5.0"
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	(release / "docs" / "RELEASE-baton-11.2.0.md").write_bytes(b"# note\n")
	(release / "docs" / "RELEASE-baton-tui-11.5.0.md").write_bytes(b"# note\n")
	assert run("publish", str(dest), "--source", str(release)).returncode == 0
	assert os.readlink(generation / "latest") == "v11.2.0"
	assert first.is_dir(), "the previous exact release was removed"

	back = run("alias", str(generation), "v11.1.0")
	assert back.returncode == 0, back.stderr
	assert os.readlink(generation / "latest") == "v11.1.0"
	assert json.loads(back.stdout)["previous"] == "v11.2.0"


def test_resolving_names_the_exact_path_to_execute(deployed):
	"""What a consumer does ONCE at launch. `latest` is never the path a
	running zipapp holds: `zipimport` reopens the archive by path on every lazy
	import, so a process that kept an alias open could read the archive that
	replaced it."""
	dest, version_dir = deployed
	resolved = run("resolve", str(version_dir.parent))
	assert resolved.returncode == 0, resolved.stderr
	printed = json.loads(resolved.stdout)
	assert printed["release"] == str(version_dir)
	assert printed["execute"] == str(version_dir / "bin" / "baton")
	assert "latest" not in printed["execute"]


def test_a_dangling_alias_is_refused_rather_than_resolved(deployed):
	dest, version_dir = deployed
	generation = version_dir.parent
	(generation / "latest").unlink()
	(generation / "latest").symlink_to("v11.9.9")
	refused = run("resolve", str(generation))
	assert refused.returncode != 0
	assert b"dangling" in refused.stderr


def test_activation_is_superseded_and_says_so(deployed):
	"""A shipped command that vanished would leave scripts failing with a
	usage error. It refuses and names its replacement instead."""
	dest, _version_dir = deployed
	refused = run("activate", str(dest), "f" * 64)
	assert refused.returncode != 0
	assert b"superseded" in refused.stderr
	assert b"alias" in refused.stderr
	assert not (dest / "current").exists()


def _tree_state(root: pathlib.Path) -> dict:
	return {str(path.relative_to(root)): _sha(path.read_bytes())
	        for path in sorted(root.rglob("*")) if path.is_file()}


def test_deploying_leaves_its_source_and_the_repository_untouched(release,
                                                                  tmp_path):
	"""Publishing reads; it must never write into what it read.

	SUPERSEDED MEASUREMENT: this used to hash the repository's `bin/baton` and
	compare it with the repository's OWN manifest. That is a self-consistency
	check, not a no-mutation check -- a publish that rewrote both files
	coherently would have passed it, and neither file is even the source this
	publish reads. Captured BEFORE and AFTER, over the whole source tree and
	over the checkout's artifacts, is the only form of this assertion that can
	fail."""
	source_before = _tree_state(release)
	checkout_before = {**_tree_state(REPO / "bin"), **_tree_state(REPO / "dist")}
	assert source_before and checkout_before, "nothing to protect"

	done = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert done.returncode == 0, done.stderr

	assert _tree_state(release) == source_before, "publishing wrote into its source"
	assert {**_tree_state(REPO / "bin"),
	        **_tree_state(REPO / "dist")} == checkout_before, \
		"publishing wrote into the checkout"


def test_a_mode_only_change_is_detected(published_set):
	"""R3. Changing `README.md` from 0444 to 0644 without touching a byte
	returned no problems at all, and activation would then accept a writable
	tree. The old tamper test changed both, so the digest was what failed it."""
	_dest, version_dir = published_set
	assert run("verify", str(version_dir)).returncode == 0
	(version_dir / "README.md").chmod(0o644)
	changed = run("verify", str(version_dir))
	assert changed.returncode != 0
	assert b"README.md: expected mode 444" in changed.stdout
	assert b"found 644" in changed.stdout


def test_a_symlinked_version_root_is_refused(published_set, tmp_path):
	"""The leaf checks stop before the root, so `verify` would have validated
	a deployment living somewhere else entirely."""
	_dest, version_dir = published_set
	pointer = tmp_path / "pointer"
	pointer.symlink_to(version_dir)
	refused = run("verify", str(pointer))
	assert refused.returncode != 0
	assert b"is a symlink" in refused.stdout


def test_a_pre_existing_staging_object_is_never_deleted(release, tmp_path):
	"""Staging is created atomically with a name this call thereby owns, so
	there is no path where the tool removes an object it did not create."""
	dest = tmp_path / "dest"
	dest.mkdir()
	stray = dest / ".staging-set-someone-else"
	stray.mkdir()
	(stray / "keep").write_text("not mine to delete\n")

	assert run("publish", str(dest), "--source", str(release)).returncode == 0
	assert (stray / "keep").exists(), "an unrelated staging object was removed"


# -- coherence, which independent versions make necessary -------------------
#
# Matching version STRINGS never proved compatibility; they proved two files
# were written in one act. These are the properties that actually decide
# whether a set can be run together, and they are checkable only because the
# manifests now attest to the core each product embeds.

def test_a_product_requiring_an_api_its_core_does_not_offer_is_refused(release,
                                                                       tmp_path):
	"""The failure independent cadences introduce: a console built against a
	core API that the core inside it no longer provides."""
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton-tui"]["requires_core_api"] = 4
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"requires core API 4" in refused.stderr
	assert b"offering API 3" in refused.stderr


def test_products_embedding_different_cores_are_refused(release, tmp_path):
	"""A set is published and activated together, so it ships one core. Before
	the attestation existed this could not even be asked."""
	catalog = json.loads(json.dumps(CATALOG))
	catalog["core"]["version"] = "1.0.0"          # a genuinely different core
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"embed different cores" in refused.stderr


@pytest.mark.parametrize("name", ["dist/DISTRIBUTION.json",
                                  "dist/DISTRIBUTION-TUI.json"])
def test_a_manifest_that_does_not_attest_its_core_is_refused(release, tmp_path, name):
	"""Each product, separately: an older builder's manifest cannot be
	published, because nothing in it says what it contains."""
	manifest = json.loads((release / name).read_text())
	# PRESENT BUT EMPTY, which a "missing key" check would let through: the
	# field has to say version, api_version and digest or it attests nothing.
	manifest["embeds_core"] = {"version": "1.1.0"}
	(release / name).write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"does not attest which core it embeds" in refused.stderr


@pytest.mark.parametrize("name", ["dist/DISTRIBUTION.json",
                                  "dist/DISTRIBUTION-TUI.json"])
def test_an_older_manifest_shape_is_named_rather_than_half_read(release, tmp_path,
                                                                name):
	"""The checked-in 1.0 manifests are exactly this shape. The refusal says
	which fields are missing and why, instead of publishing a set whose record
	has holes in it."""
	(release / name).write_text(json.dumps({
		"tool": "baton", "artifact": "bin/baton",
		"artifact_sha256": "00" * 32,
		"release_version": "1.0.0", "protocol_version": 10}))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"product_version" in refused.stderr
	assert b"predates independently versioned products" in refused.stderr


def test_the_set_digest_changes_when_any_certified_fact_changes(release, tmp_path):
	"""It identifies the SET, so it must move when the set does -- and a
	digest that ignored a product version would name two different sets the
	same thing."""
	import deploy

	before = deploy.certified(str(release))["set_digest"]
	# BOTH products, because the catalog they share IS part of the core they
	# both embed: bumping one version rebuilds the other's core too, which is
	# exactly what a real release does.
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton-tui"]["version"] = "1.5.0"
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	(release / "docs" / "RELEASE-baton-tui-1.5.0.md").write_bytes(b"# 1.5.0\n")
	after = deploy.certified(str(release))["set_digest"]
	assert before != after


# -- legacy records stay verifiable ----------------------------------------

def test_a_version_1_record_still_verifies_read_only(published_set):
	"""A destination is a live directory somebody's `current` points into.
	Retiring their ability to check it is not an upgrade, so the old record
	shape is still READ -- its digests and modes mean exactly what they meant
	when it was written. What is retired is WRITING it: publish only produces
	version 2."""
	import deploy

	dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	legacy = {"release_version": "1.0.0", "protocol_version": 10,
	          "files": record["files"]}
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(legacy, indent=2, sort_keys=True) + "\n")
	record_path.chmod(0o444)

	problems = deploy.verify(str(version_dir))
	# The record itself is a recorded file, so rewriting it is a digest
	# mismatch on exactly that file -- and nothing else.
	assert all("DEPLOYMENT.json" in problem for problem in problems), problems
	assert deploy._deployed_products(str(version_dir)) == {"release_version": "1.0.0"}


def test_an_unknown_record_version_is_refused_rather_than_guessed(published_set):
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	record["record_version"] = 99
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)
	problems = deploy.verify(str(version_dir))
	assert any("record version 99" in problem for problem in problems), problems


# -- the set digest identifies the whole set -------------------------------
#
# It once hashed the protocol and a reduced product summary, so a tree that
# differed in a document, a note, the example config or a manifest field alone
# landed at the same immutable `set-<digest>` path -- and the second publish
# reported it as the set that was already there.

@pytest.mark.parametrize("path,change", [
	("README.md", b"# baton, but different\n"),
	("docs/EFFECTIVE-BATON.md", b"# using it, revised\n"),
	("docs/AGENTS-MAILBOX-PROTO.md", b"# the protocol, amended\n"),
	("docs/RELEASE-baton-11.1.0.md", b"# baton 11.1.0, reworded\n"),
	("LICENSE", b"a different licence\n"),
])
def test_the_set_digest_covers_every_payload_file(release, tmp_path, path, change):
	import deploy

	before = deploy.certified(str(release))["set_digest"]
	(release / path).write_bytes(change)
	if path == "docs/AGENTS-MAILBOX-PROTO.md":
		# The document is hash-pinned by both manifests, so repin it: this test
		# is about the SET identity, not about the pin that already worked.
		for name in ("DISTRIBUTION.json", "DISTRIBUTION-TUI.json"):
			manifest = json.loads((release / "dist" / name).read_text())
			manifest["protocol_doc_sha256"] = _sha(change)
			(release / "dist" / name).write_text(json.dumps(manifest))
	assert deploy.certified(str(release))["set_digest"] != before, path


def test_the_set_digest_covers_the_example_config(release, tmp_path):
	import deploy

	before = deploy.certified(str(release))["set_digest"]
	template = json.loads((release / "examples" / "baton.json").read_text())
	template["retention_days"] = 30
	(release / "examples" / "baton.json").write_text(json.dumps(template))
	assert deploy.certified(str(release))["set_digest"] != before


def test_the_set_digest_covers_manifest_only_fields(release, tmp_path):
	"""A field nobody copies into the payload -- the embedded-core version --
	still changes what this set IS."""
	import deploy

	before = deploy.certified(str(release))["set_digest"]
	catalog = json.loads(json.dumps(CATALOG))
	catalog["core"]["version"] = "1.2.0"
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	assert deploy.certified(str(release))["set_digest"] != before


def test_a_changed_document_installs_as_a_different_candidate(release, tmp_path):
	"""The set digest is provenance now, not a pathname — and it still answers
	the question it always answered: two candidates that differ anywhere are
	not the same candidate, whatever their product versions say."""
	dest = tmp_path / "dest"
	assert run("publish", str(dest), "--source", str(release)).returncode == 0
	before = json.loads(
		(release_dir(dest, release) / "PRODUCT.json").read_text())

	(release / "docs" / "EFFECTIVE-BATON.md").write_bytes(b"# reworded\n")
	after_digest = deploy_digest(release)
	assert after_digest != before["provenance"]["set_digest"]

	# The version did not change, so the exact release is the same path -- and
	# its bytes are not the same bytes. That is refused, not overwritten.
	refused = run("publish", str(dest), "--source", str(release))
	assert refused.returncode != 0
	assert b"describes a DIFFERENT" in refused.stderr
	assert json.loads((release_dir(dest, release) / "PRODUCT.json").read_text()) \
		== before


def test_a_set_directory_that_records_another_set_still_fails_verify(
		published_set, tmp_path):
	"""The superseded layout, still READ. A set directory renamed to claim a
	different digest fails its own identity, which is what made the digest
	worth having as a name -- and is why it survives as provenance."""
	dest, version_dir = published_set
	other = dest / ("set-" + "b" * 64)
	version_dir.rename(other)
	problems = run("verify", str(other))
	assert problems.returncode != 0
	assert b"set_digest" in problems.stdout or b"directory" in problems.stdout


def test_the_record_carries_the_manifests_it_is_identified_by(published_set):
	"""The identity must be recomputable from the deployed tree ALONE -- that
	is what lets `verify` ask a directory whether its own name is honest, with
	no source tree anywhere. Dropping the manifests from the record takes that
	away."""
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	assert set(record["manifests"]) == {"dist/DISTRIBUTION.json",
	                                    "dist/DISTRIBUTION-TUI.json"}
	assert record["manifests"]["dist/DISTRIBUTION-TUI.json"]["product_version"] \
		== "11.4.0"
	# And it is the input the digest is over: recomputing from the record
	# reproduces the name.
	assert deploy.set_digest(record["protocol_version"], record["manifests"],
	                         record["files"]) == version_dir.name[len("set-"):]

	del record["manifests"]
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)
	problems = deploy.verify(str(version_dir))
	assert any("must carry manifests and products" in p for p in problems), problems


def test_a_version_2_record_missing_its_version_is_refused_not_downgraded(published_set):
	"""Defaulting a missing `record_version` to 1 meant deleting one key turned
	every identity check off, because legacy records have no identity."""
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	del record["record_version"]
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)
	problems = deploy.verify(str(version_dir))
	assert any("no record_version" in p for p in problems), problems


# -- each manifest is bound to the product it must describe ----------------

def test_a_manifest_describing_the_wrong_product_is_refused(release, tmp_path):
	manifest = json.loads((release / "dist" / "DISTRIBUTION-TUI.json").read_text())
	manifest["tool"] = "baton"
	(release / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"expects it to describe 'baton-tui'" in refused.stderr


def test_two_manifests_claiming_one_product_cannot_collapse(release, tmp_path):
	"""They used to share a dictionary key: the later overwrote the earlier,
	coherence examined one artifact, and the set digest identified one of two."""
	cli = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	cli["tool"] = "baton-tui"
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(cli))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"expects it to describe 'baton'" in refused.stderr


def test_two_products_naming_one_artifact_are_refused(release, tmp_path):
	# A COHERENT collision: the console's catalog really names the CLI's path,
	# so the artifact attestation passes and the duplicate is what refuses.
	catalog = json.loads(json.dumps(CATALOG))
	catalog["products"]["baton-tui"]["artifact"] = "bin/baton"
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"two products cannot be one file" in refused.stderr


@pytest.mark.parametrize("field", ["artifact", "protocol_doc"])
@pytest.mark.parametrize("path", ["/etc/passwd", "../outside/bin/baton",
                                  "bin/../../escape", "~/bin/baton",
                                  "bin\\baton"])
def test_a_manifest_path_that_escapes_the_root_is_refused(release, tmp_path,
                                                          field, path):
	"""This string is joined to a root and then opened. `/etc/passwd` arriving
	at that join is the difference between a manifest and an instruction."""
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest[field] = path
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0, path
	assert b"relative POSIX path" in refused.stderr \
		or b"dotted component" in refused.stderr, refused.stderr


# -- the artifact is asked whether the manifest is telling the truth -------
#
# Matching the whole-file digest proves a manifest describes THESE bytes. It
# proves nothing about what the manifest SAYS they are: a relabelled version, a
# different protocol, a false embedded core — none of them changes a byte of
# the archive, so all of them certified. The archive carries the catalog it was
# built from, so every claim is checkable against the thing it claims about.

def test_a_false_core_identity_in_both_manifests_is_refused(release, tmp_path):
	"""The reproduced defect: changing BOTH manifests to the same false core
	kept them agreeing with each other, and agreement was all that was
	checked."""
	false = {"version": "9.9.9", "api_version": 3, "package_sha256": "ab" * 32}
	for name in ("DISTRIBUTION.json", "DISTRIBUTION-TUI.json"):
		manifest = json.loads((release / "dist" / name).read_text())
		manifest["embeds_core"] = false
		(release / "dist" / name).write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"claims to embed core 9.9.9" in refused.stderr


def test_a_relabelled_product_version_is_refused(release, tmp_path):
	"""Same artifact bytes, a different number on the box — and a different
	release note selected to go with it."""
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest["product_version"] = "2.0.0"
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	(release / "docs" / "RELEASE-baton-2.0.0.md").write_bytes(b"# baton 2.0.0\n")
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"claims product_version='2.0.0'" in refused.stderr


@pytest.mark.parametrize("field,value", [
	("protocol_version", 12),
	("requires_core_api", 4),
	("python_min", "3.99"),
	("sqlite_min", "9.9.9"),
	("artifact", "bin/elsewhere"),
])
def test_a_claim_the_artifact_contradicts_is_refused(release, tmp_path, field, value):
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest[field] = value
	if field == "artifact":
		(release / "bin" / "elsewhere").write_bytes(
			(release / "bin" / "baton").read_bytes())
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0, field
	assert b"carries" in refused.stderr, refused.stderr


def test_two_different_cores_cannot_claim_one_digest(release, tmp_path):
	"""The console really carries a different core; both manifests claim the
	CLI's digest. Recomputation from the archive is what tells them apart."""
	# The console's core carries one EXTRA member: same declared version, and
	# therefore a different digest -- which is the only thing that can tell
	# them apart, and the reason the digest is recomputed from the archive.
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui",
	        extra={"baton_core/extra.py": b"# one more member\n"})
	cli = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	tui = json.loads((release / "dist" / "DISTRIBUTION-TUI.json").read_text())
	tui["embeds_core"] = cli["embeds_core"]         # claim the CLI's core
	(release / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps(tui))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"contains" in refused.stderr


def test_the_cli_source_pin_is_checked_against_the_archive(release, tmp_path):
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest["source_sha256"] = "cd" * 32
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"pins source_sha256" in refused.stderr


def test_the_console_member_list_is_checked_against_the_archive(release, tmp_path):
	manifest = json.loads((release / "dist" / "DISTRIBUTION-TUI.json").read_text())
	manifest["members"] = manifest["members"] + ["baton_tui/imaginary.py"]
	(release / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"lists members that are not what" in refused.stderr


def test_an_artifact_that_is_not_a_zipapp_is_refused(release, tmp_path):
	(release / "bin" / "baton").write_bytes(b"#!/bin/sh\necho not a zipapp\n")
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest["artifact_sha256"] = _sha((release / "bin" / "baton").read_bytes())
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"not a readable zipapp" in refused.stderr


def test_an_artifact_carrying_no_catalog_cannot_be_certified(release, tmp_path):
	"""It cannot say what it is, so nothing it is labelled with can be
	checked."""
	import io
	import zipfile

	buffer = io.BytesIO()
	buffer.write(b"#!/usr/bin/env python3\n")
	with zipfile.ZipFile(buffer, "w") as archive:
		archive.writestr("__main__.py", "# nothing else\n")
	payload = buffer.getvalue()
	(release / "bin" / "baton").write_bytes(payload)
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest["artifact_sha256"] = _sha(payload)
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"carries no baton_core/products.json" in refused.stderr


# -- a deployment record may not address outside its own tree --------------

@pytest.mark.parametrize("escape", [
	"../outside-secret", "/etc/passwd", "bin/../../escape", "",
	"./bin/baton", "bin//baton", "bin\\baton",
])
def test_a_record_path_that_escapes_the_tree_is_refused(published_set, tmp_path, escape):
	"""The reproduced defect: `files` keys went straight to `os.path.join`
	against the deployment root, so a record naming `../outside-secret` with
	that file's digest verified successfully. The record became an instruction
	to read outside the tree."""
	import deploy

	_dest, version_dir = published_set
	outside = tmp_path / "outside-secret"
	outside.write_bytes(b"not part of any deployment\n")

	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	record["files"][escape] = _sha(outside.read_bytes())
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)

	problems = deploy.verify(str(version_dir))
	assert problems, escape
	assert all("files entry" in p for p in problems), (escape, problems)


def test_a_record_digest_that_is_not_a_digest_is_refused(published_set):
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	record["files"]["README.md"] = "not-a-digest"
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)
	problems = deploy.verify(str(version_dir))
	assert any("is not a sha256 digest" in p for p in problems), problems


def test_no_outside_path_is_opened_while_verifying(published_set, tmp_path, monkeypatch):
	"""The probe: whatever the record says, `verify` must not reach outside the
	tree it was pointed at."""
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record = json.loads(record_path.read_text())
	record["files"]["../outside-secret"] = "00" * 32
	record_path.chmod(0o644)
	record_path.write_text(json.dumps(record))
	record_path.chmod(0o444)

	opened = []
	real_open = deploy.os.open

	def watched(path, *args, **kwargs):
		opened.append(str(path))
		return real_open(path, *args, **kwargs)
	monkeypatch.setattr(deploy.os, "open", watched)
	deploy.verify(str(version_dir))
	monkeypatch.undo()
	root = os.path.abspath(version_dir)
	assert opened, "the probe never saw an open at all"
	for path in opened:
		assert os.path.abspath(path).startswith(root), path


# -- malformed trust documents refuse, and do not traceback ----------------

@pytest.mark.parametrize("field,value", [
	("product_version", 110),
	("product_version", "1.1"),
	("artifact_sha256", 12345),
	("artifact_sha256", "ABAB" * 16),
	("protocol_version", "10"),
	("tool", 7),
	("python_min", 3.11),
	("members", "not-a-list"),
	("source_sha256", "short"),
	("embeds_core", "not-an-object"),
])
def test_a_malformed_manifest_field_refuses_without_a_traceback(release, tmp_path,
                                                                field, value):
	name = "DISTRIBUTION-TUI.json" if field == "members" else "DISTRIBUTION.json"
	manifest = json.loads((release / "dist" / name).read_text())
	manifest[field] = value
	(release / "dist" / name).write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0, (field, value)
	assert b"Traceback" not in refused.stderr, refused.stderr
	assert refused.stderr.startswith(b"deploy: "), refused.stderr


@pytest.mark.parametrize("field", ["protocol_version", "requires_core_api"])
def test_a_boolean_is_not_an_integer(release, tmp_path, field):
	"""`True == 1` in Python, so `protocol_version: true` compares equal to
	protocol 1 and would travel into the set identity as a plausible fact. The
	refusal has to name the TYPE, or a later comparison masks it and the check
	can be deleted without any test noticing."""
	manifest = json.loads((release / "dist" / "DISTRIBUTION.json").read_text())
	manifest[field] = True
	(release / "dist" / "DISTRIBUTION.json").write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert f"{field} is not an integer".encode() in refused.stderr, refused.stderr


@pytest.mark.parametrize("name,tool,fields", [
	("DISTRIBUTION.json", "baton", ("source_sha256",)),
	("DISTRIBUTION-TUI.json", "baton-tui", ("members",)),
	("DISTRIBUTION.json", "baton", ("protocol_doc", "protocol_doc_sha256")),
	("DISTRIBUTION-TUI.json", "baton-tui", ("protocol_doc", "protocol_doc_sha256")),
	("DISTRIBUTION.json", "baton", ("protocol_doc_sha256",)),
	("DISTRIBUTION.json", "baton", ("protocol_doc",)),
])
def test_deleting_a_generated_attestation_is_refused(release, tmp_path, name,
                                                     tool, fields):
	"""Every one of these is emitted by its builder and described here as a
	certified fact. They were type-checked WHEN PRESENT and absent without
	complaint, so deleting one quietly removed a check -- a pin with no digest
	is a pin that does not pin, and a manifest with neither field certifies a
	distribution whose protocol document nothing looked at."""
	manifest = json.loads((release / "dist" / name).read_text())
	for field in fields:
		del manifest[field]
	(release / "dist" / name).write_text(json.dumps(manifest))
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0, fields
	assert b"is missing" in refused.stderr, refused.stderr
	assert b"Traceback" not in refused.stderr


def test_malformed_manifest_json_refuses_by_name(release, tmp_path):
	(release / "dist" / "DISTRIBUTION.json").write_text("{ not json at all")
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert b"not readable JSON" in refused.stderr
	assert b"Traceback" not in refused.stderr


def test_malformed_record_json_refuses_by_name(published_set):
	import deploy

	_dest, version_dir = published_set
	record_path = version_dir / "DEPLOYMENT.json"
	record_path.chmod(0o644)
	record_path.write_text("{ not json at all")
	record_path.chmod(0o444)
	problems = deploy.verify(str(version_dir))
	assert any("not readable JSON" in p for p in problems), problems


# -- the artifact must be able to read its own identity --------------------

@pytest.mark.parametrize("change,marker", [
	({"format": "unknown.products"}, b"format 'unknown.products'"),
	({"format_version": 99}, b"catalog format version 99"),
	({"format_version": "1"}, b"catalog format version '1'"),
])
def test_an_artifact_whose_catalog_this_reader_cannot_load_is_refused(
		release, tmp_path, change, marker):
	"""The runtime reader refuses a document format it does not understand, so
	certifying such an artifact publishes something that cannot say what it is
	— it would fail at startup, having been declared fit to run."""
	catalog = json.loads(json.dumps(CATALOG))
	catalog.update(change)
	rebuild(release, "DISTRIBUTION.json", "baton", catalog=catalog)
	rebuild(release, "DISTRIBUTION-TUI.json", "baton-tui", catalog=catalog)
	refused = run("publish", str(tmp_path / "dest"), "--source", str(release))
	assert refused.returncode != 0
	assert marker in refused.stderr, refused.stderr
	assert b"Traceback" not in refused.stderr


def test_the_deployer_and_the_core_agree_on_the_catalog_contract():
	"""The deployer restates the contract because it certifies distributions
	rather than this repository, and cannot import the core it is checking.
	This is what stops the restatement from drifting."""
	import sys as _sys

	_sys.path.insert(0, str(REPO / "src"))
	from baton_core import products
	import deploy

	assert deploy.CATALOG_FORMAT == products.SUPPORTED_FORMAT
	assert deploy.CATALOG_FORMAT_VERSIONS == products.SUPPORTED_FORMAT_VERSIONS
	assert deploy.CATALOG_MEMBER == f"baton_core/{products.CATALOG_NAME}"
