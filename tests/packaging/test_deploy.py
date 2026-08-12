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


@pytest.fixture
def release(tmp_path):
	"""A minimal, internally consistent release tree.

	Built rather than copied so a test can make exactly one thing wrong and
	watch the gate refuse it."""
	source = tmp_path / "source"
	(source / "bin").mkdir(parents=True)
	(source / "docs").mkdir()
	(source / "dist").mkdir()
	(source / "examples").mkdir()

	cli = b"#!/usr/bin/env python3\n# pretend cli\n"
	tui = b"#!/usr/bin/env python3\n# pretend console\n"
	proto = b"# the protocol\n"
	(source / "bin" / "baton").write_bytes(cli)
	(source / "bin" / "baton-tui").write_bytes(tui)
	(source / "docs" / "AGENTS-MAILBOX-PROTO.md").write_bytes(proto)
	(source / "docs" / "EFFECTIVE-BATON.md").write_bytes(b"# using it\n")
	(source / "docs" / "RELEASE-1.1.0.md").write_bytes(b"# 1.1.0 is out\n")
	(source / "README.md").write_bytes(b"# baton\n")
	(source / "LICENSE").write_bytes(b"a licence\n")
	(source / "examples" / "baton.json").write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "example"},
		"participants": {"team.implementer": {}, "team.reviewer": {}},
		"roots": {}, "retention_days": 90}))
	(source / "dist" / "DISTRIBUTION.json").write_text(json.dumps({
		"tool": "baton", "artifact": "bin/baton", "artifact_sha256": _sha(cli),
		"release_version": "1.1.0", "protocol_version": 10,
		"protocol_doc": "docs/AGENTS-MAILBOX-PROTO.md",
		"protocol_doc_sha256": _sha(proto)}, indent=2))
	(source / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps({
		"tool": "baton-tui", "artifact": "bin/baton-tui",
		"artifact_sha256": _sha(tui),
		"release_version": "1.1.0", "protocol_version": 10}, indent=2))
	return source


@pytest.fixture
def deployed(release, tmp_path):
	dest = tmp_path / "deploy"
	done = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert done.returncode == 0, done.stderr
	return dest, dest / "v1.1.0"


# -- the ruled command and payload ----------------------------------------

def test_publish_requires_the_version_the_human_intends(release, tmp_path):
	"""R1. `just deploy DEST 1.1.0` — the operator states the release, and the
	tool refuses unless the manifests say exactly that. Deploying "whatever the
	manifests happen to name" cannot answer the only question they have."""
	dest = tmp_path / "dest"
	wrong = run("publish", str(dest), "1.0.0", "--source", str(release))
	assert wrong.returncode != 0
	assert b"names release 1.1.0" in wrong.stderr
	assert not dest.exists() or list(dest.iterdir()) == []

	malformed = run("publish", str(dest), "v1.1", "--source", str(release))
	assert malformed.returncode != 0
	assert b"major.minor.patch" in malformed.stderr

	assert run("publish", str(dest), "1.1.0", "--source", str(release)).returncode == 0
	assert (dest / "v1.1.0").is_dir()


def test_the_release_document_follows_the_version(release, tmp_path):
	"""Hardcoding `RELEASE-1.0.0.md` would ship the previous announcement, or
	fail once it was retired."""
	dest = tmp_path / "dest"
	assert run("publish", str(dest), "1.1.0", "--source", str(release)).returncode == 0
	assert (dest / "v1.1.0" / "docs" / "RELEASE-1.1.0.md").exists()
	assert not (dest / "v1.1.0" / "docs" / "RELEASE-1.0.0.md").exists()

	(release / "docs" / "RELEASE-1.1.0.md").unlink()
	missing = run("publish", str(tmp_path / "other"), "1.1.0", "--source", str(release))
	assert missing.returncode != 0
	assert b"RELEASE-1.1.0.md is missing" in missing.stderr


def test_the_example_config_ships_and_stays_inert(deployed, release, tmp_path):
	"""Ruled: the template ships. It is a config SHAPE to copy — and publish
	proves it names no live authority, because a config inside a deployment is
	a config someone will point at."""
	_dest, version_dir = deployed
	shipped = version_dir / "examples" / "baton.json"
	assert shipped.exists()
	document = json.loads(shipped.read_text())
	assert "participants" in document
	assert document["roots"] == {}

	# No authority, and nothing that looks like one, anywhere in the tree.
	assert list(version_dir.rglob("*.sqlite3")) == []
	assert [p for p in version_dir.rglob("baton.json")
	        if p.parent.name != "examples"] == []

	# A template naming a real authority is refused.
	live = tmp_path / "live-root"
	live.mkdir()
	(release / "examples" / "baton.json").write_text(json.dumps({
		"config_version": 1, "protocol_version": 10, "generation": 1,
		"mailbox": {"name": "x"}, "participants": {},
		"roots": {"src": str(live)}, "retention_days": 90}))
	refused = run("publish", str(tmp_path / "other"), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"points at an existing absolute root" in refused.stderr


# -- certification ----------------------------------------------------------

def test_a_manifest_pinned_protocol_document_is_certified(release, tmp_path):
	"""R2. Only the artifacts were checked, so 1.0 binaries could be paired
	with newer protocol prose and blessed by a record written over the
	mixture — whose own later `verify` would then pass."""
	(release / "docs" / "AGENTS-MAILBOX-PROTO.md").write_bytes(b"# moved on\n")
	dest = tmp_path / "dest"
	refused = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"does not match the hash pinned" in refused.stderr
	assert not dest.exists() or list(dest.iterdir()) == [], \
		"a refused publish left a destination version behind"


def test_the_manifests_must_agree_on_the_protocol(release, tmp_path):
	tui = json.loads((release / "dist" / "DISTRIBUTION-TUI.json").read_text())
	tui["protocol_version"] = 11
	(release / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps(tui))
	refused = run("publish", str(tmp_path / "dest"), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"disagree on the protocol version" in refused.stderr


def test_publishing_refuses_an_uncertified_artifact(release, tmp_path):
	artifact = release / "bin" / "baton"
	artifact.write_bytes(artifact.read_bytes() + b"\n# not the certified bytes\n")
	dest = tmp_path / "dest"
	out = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert out.returncode != 0
	assert b"not certified" in out.stderr
	assert not dest.exists() or list(dest.iterdir()) == []


# -- nothing partial ever appears ------------------------------------------

def test_a_missing_late_payload_file_leaves_no_version_behind(release, tmp_path):
	"""R3, reproduced: the old tool filled the final directory as it copied,
	so a missing LICENSE left a partial `v1.1.0` that the immutability rule
	then blocked anyone from repairing."""
	(release / "LICENSE").unlink()
	dest = tmp_path / "dest"
	refused = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"LICENSE is missing" in refused.stderr
	assert not (dest / "v1.1.0").exists(), "a partial version was published"
	assert [p.name for p in dest.iterdir()] == [] if dest.exists() else True


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
		deploy.publish(str(release), str(dest), "1.1.0")

	assert not (dest / "v1.1.0").exists(), "a partial version survived"
	leftovers = [p.name for p in dest.iterdir()] if dest.exists() else []
	assert leftovers == [], f"staging or lock left behind: {leftovers}"


def test_an_existing_empty_directory_is_never_replaced(release, tmp_path):
	"""`rename` would happily consume an empty directory. A version somebody
	else created, however empty, is not this tool's to overwrite."""
	dest = tmp_path / "dest"
	(dest / "v1.1.0").mkdir(parents=True)
	refused = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"never rewritten in place" in refused.stderr
	assert list((dest / "v1.1.0").iterdir()) == [], "the empty directory was written into"


def test_a_second_publish_of_the_same_version_is_refused(deployed, release):
	dest, _version_dir = deployed
	again = run("publish", str(dest), "1.1.0", "--source", str(release))
	assert again.returncode != 0
	assert b"never rewritten in place" in again.stderr


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
		deploy.publish(str(release), str(dest), "1.1.0")
	assert "never rewritten in place" in str(refused.value)
	assert list((dest / "v1.1.0").iterdir()) == [], "the directory was written into"
	assert not list(dest.glob(".staging-*")), "staging survived the refusal"


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
		deploy.publish(str(release), str(dest), "1.1.0")
	assert "atomic no-replace" in str(refused.value)
	assert not (dest / "v1.1.0").exists()
	assert not list(dest.glob(".staging-*"))


def test_a_failure_after_hardening_still_removes_only_its_own_staging(release,
                                                                     tmp_path,
                                                                     monkeypatch):
	"""R2. `_harden` makes every staging directory `0555`, so an ordinary
	`rmtree` could not unlink anything inside them: a failure at the final
	rename left the whole hardened tree behind. The earlier copy-failure test
	failed BEFORE hardening and never reached this path."""
	import deploy

	dest = tmp_path / "dest"
	dest.mkdir()
	unrelated = dest / ".staging-v1.1.0-99999"
	unrelated.mkdir()
	(unrelated / "someone-elses-work").write_text("do not delete me\n")

	def explode(source, target):
		raise OSError("the rename failed after hardening")

	monkeypatch.setattr(deploy, "_rename_noreplace", explode)
	with pytest.raises(OSError):
		deploy.publish(str(release), str(dest), "1.1.0")

	assert (unrelated / "someone-elses-work").exists(), \
		"an unrelated staging directory was deleted"
	mine = [p for p in dest.glob(".staging-*") if p != unrelated]
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
	deploy.publish(str(release), str(dest), "1.1.0")

	staged = [p for p in synced if ".staging-v1.1.0-" in p]
	for nested in ("bin", "docs", "dist", "examples"):
		assert any(p.endswith("/" + nested) for p in staged), \
			f"{nested} was never fsynced: {staged}"
	assert any(p.rstrip("/").endswith("dest") for p in synced), \
		"the destination directory was not fsynced"


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


def test_verification_detects_tampering_extra_files_and_symlinks(deployed, tmp_path):
	_dest, version_dir = deployed
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
	refused = run("publish", str(tmp_path / "dest"), "1.1.0", "--source", str(release))
	assert refused.returncode != 0
	assert b"symlink" in refused.stderr


def test_the_record_is_reproducible(release, tmp_path):
	"""No timestamps inside the tree, so two people deploying one release get
	identical trees and verification can be exact."""
	records = []
	for name in ("a", "b"):
		dest = tmp_path / name
		assert run("publish", str(dest), "1.1.0", "--source", str(release)).returncode == 0
		records.append((dest / "v1.1.0" / "DEPLOYMENT.json").read_bytes())
	assert records[0] == records[1]
	record = json.loads(records[0])
	assert record["release_version"] == "1.1.0"
	assert record["protocol_version"] == 10


# -- activation -------------------------------------------------------------

def test_activation_is_atomic_relative_and_verified(deployed):
	dest, version_dir = deployed
	assert run("activate", str(dest), "1.1.0").returncode == 0
	link = dest / "current"
	assert link.is_symlink() and os.readlink(link) == "v1.1.0"
	assert not os.path.isabs(os.readlink(link)), \
		"an absolute link breaks if the root is moved or mounted elsewhere"
	assert (link / "bin" / "baton").exists()
	assert not list(dest.glob(".current-*")), "a staging link survived"

	readme = version_dir / "README.md"
	readme.chmod(0o644)
	readme.write_text("tampered\n")
	refused = run("activate", str(dest), "1.1.0")
	assert refused.returncode != 0 and b"does not verify" in refused.stderr
	assert os.readlink(link) == "v1.1.0", "a refusal disturbed the pointer"


def test_activation_refuses_rather_than_deleting_unrelated_objects(deployed):
	"""The old version `os.remove()`d whatever sat at a fixed staging name and
	let `rename` replace a regular file at `current`. A shipped command must
	not delete objects it did not create."""
	dest, _version_dir = deployed
	precious = dest / "current"
	precious.write_text("somebody's notes\n")
	refused = run("activate", str(dest), "1.1.0")
	assert refused.returncode != 0
	assert b"not a symlink" in refused.stderr
	assert precious.read_text() == "somebody's notes\n", "an unrelated file was replaced"


def test_activating_an_undeployed_version_is_refused(deployed):
	dest, _version_dir = deployed
	refused = run("activate", str(dest), "9.9.9")
	assert refused.returncode != 0
	assert b"not a deployed version directory" in refused.stderr


def test_deploying_leaves_the_repository_untouched(deployed):
	"""Publishing reads; it must never write into the source."""
	published = json.loads((REPO / "dist" / "DISTRIBUTION.json").read_text())
	assert hashlib.sha256((REPO / "bin" / "baton").read_bytes()).hexdigest() == \
		published["artifact_sha256"], "publishing perturbed the repository's artifact"


def test_a_mode_only_change_is_detected(deployed):
	"""R3. Changing `README.md` from 0444 to 0644 without touching a byte
	returned no problems at all, and activation would then accept a writable
	tree. The old tamper test changed both, so the digest was what failed it."""
	_dest, version_dir = deployed
	assert run("verify", str(version_dir)).returncode == 0
	(version_dir / "README.md").chmod(0o644)
	changed = run("verify", str(version_dir))
	assert changed.returncode != 0
	assert b"README.md: expected mode 444" in changed.stdout
	assert b"found 644" in changed.stdout


def test_a_symlinked_version_root_is_refused(deployed, tmp_path):
	"""The leaf checks stop before the root, so `verify` would have validated
	a deployment living somewhere else entirely."""
	_dest, version_dir = deployed
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
	stray = dest / ".staging-v1.1.0-someone-else"
	stray.mkdir()
	(stray / "keep").write_text("not mine to delete\n")

	assert run("publish", str(dest), "1.1.0", "--source", str(release)).returncode == 0
	assert (stray / "keep").exists(), "an unrelated staging object was removed"
