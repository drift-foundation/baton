"""W4: the v11 executable is a REPRODUCIBLE artifact.

Two deployments of byte-identical sources produced different
`archive_sha256` values. `zipapp.create_archive` stamps every member with
its staging mtime, so the digest described the build's clock as much as
its inputs — and a digest that cannot prove reproduction of a reviewed
candidate is not a release gate.

The recorded evidence caught only generated `__main__.py`, because the
copied sources kept their mtimes between two builds inside one checkout.
That was luck, not scope: a fresh clone or a single touched file moves
the other thirteen members too. These checks therefore pin the property
metadata-wide rather than for the one member the evidence happened to
expose.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys
import types
import zipfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
DEPLOYER = os.path.join(REPO, "tools", "deploy_work.py")


def _deployer():
	"""Load the deployer from its SOURCE BYTES every time.

	`spec_from_file_location` goes through `SourceFileLoader`, which
	honours `__pycache__`. A cached `.pyc` is reused when the source's
	(mtime, size) match what it recorded — and a same-second edit that
	does not change the file's length satisfies both. This test asserts
	on constants defined in that source, so a stale cache would let it
	report on code that is no longer on disk. Observed exactly that
	while break-sweeping a one-digit mode change."""
	source = pathlib.Path(DEPLOYER).read_text(encoding="utf-8")
	module = types.ModuleType("deploy_work")
	module.__file__ = DEPLOYER
	exec(compile(source, DEPLOYER, "exec"), module.__dict__)
	return module


def _digest(path):
	with open(path, "rb") as handle:
		return hashlib.sha256(handle.read()).hexdigest()


def _staging(root, mtime):
	"""A miniature package tree whose every file carries `mtime`."""
	package = os.path.join(root, "baton_work")
	os.makedirs(os.path.join(package, "tui"))
	files = {
		os.path.join(package, "__init__.py"): b"VERSION = 11\n",
		os.path.join(package, "cli.py"): b"def entry():\n\treturn 0\n",
		os.path.join(package, "tui", "app.py"): b"# console\n",
	}
	for path, payload in files.items():
		with open(path, "wb") as handle:
			handle.write(payload)
		os.utime(path, (mtime, mtime))
	for base, dirs, _files in os.walk(root):
		for name in dirs:
			os.utime(os.path.join(base, name), (mtime, mtime))
	return root


# -- the property, at the writer -------------------------------------------

def test_identical_sources_with_different_mtimes_build_identical_bytes(
		tmp_path):
	"""The exact defect: same inputs, different clock, different bytes."""
	deploy = _deployer()
	first = os.path.join(str(tmp_path), "one")
	second = os.path.join(str(tmp_path), "two")
	_staging(first, 1_000_000_000)
	_staging(second, 1_700_000_000)
	a = os.path.join(str(tmp_path), "a")
	b = os.path.join(str(tmp_path), "b")
	deploy._write_zipapp(first, a)
	deploy._write_zipapp(second, b)
	with open(a, "rb") as ha, open(b, "rb") as hb:
		assert ha.read() == hb.read(), \
			"a 700-million-second mtime difference changed the artifact"


def test_every_member_carries_fixed_metadata(tmp_path):
	"""Not just the generated member — the whole archive, or a fresh
	clone reintroduces the defect through the other thirteen."""
	deploy = _deployer()
	staging = _staging(os.path.join(str(tmp_path), "src"), 1_234_567_890)
	archive = os.path.join(str(tmp_path), "baton")
	deploy._write_zipapp(staging, archive)
	with zipfile.ZipFile(archive) as bundle:
		infos = bundle.infolist()
	assert {info.date_time for info in infos} == {deploy.FIXED_DATE}
	# create_system otherwise comes from the BUILD HOST, so identical
	# sources would differ between a Linux and a Windows builder.
	assert {info.create_system for info in infos} == {3}
	assert {info.compress_type for info in infos} == {zipfile.ZIP_STORED}
	# MODES, per member kind. This is the only assertion that can tell
	# the intentional constants apart from an accidental return to
	# host-derived defaults: `ZipInfo.from_file` would copy the staging
	# file's mode, which varies with the builder's umask, so identical
	# sources under a different umask would produce a different archive.
	dirs = [info for info in infos if info.filename.endswith("/")]
	files = [info for info in infos if not info.filename.endswith("/")]
	assert dirs and files, [info.filename for info in infos]
	assert {info.external_attr for info in dirs} == {deploy.DIR_ATTR}
	assert {info.external_attr for info in files} == {deploy.FILE_ATTR}
	# ...and against the LITERAL modes, not only the module's own
	# constants. Comparing solely to `deploy.FILE_ATTR` is partly
	# self-referential: editing the constant moves both sides of that
	# equality, so a silent mode change would ship green. These pin what
	# the modes actually are — 0644 for files, 0755 for directories.
	assert deploy.FILE_ATTR == (0o100644 << 16), oct(deploy.FILE_ATTR)
	assert deploy.DIR_ATTR == (0o040755 << 16) | 0x10, oct(deploy.DIR_ATTR)
	assert {info.external_attr >> 16 for info in files} == {0o100644}
	assert {info.external_attr >> 16 for info in dirs} == {0o040755}


def test_members_are_written_in_one_sorted_order(tmp_path):
	"""os.walk order is filesystem-dependent, so enumeration is sorted
	rather than trusted."""
	deploy = _deployer()
	staging = _staging(os.path.join(str(tmp_path), "src"), 1_234_567_890)
	archive = os.path.join(str(tmp_path), "baton")
	deploy._write_zipapp(staging, archive)
	with zipfile.ZipFile(archive) as bundle:
		names = [info.filename for info in bundle.infolist()]
	assert names == sorted(names), names


def test_the_bootstrap_and_executable_shape_are_unchanged(tmp_path):
	"""The ruled entry point: cli:entry, NOT cli:main — zipapp discards
	the target's return value, which turned refusals into exit 0."""
	deploy = _deployer()
	staging = _staging(os.path.join(str(tmp_path), "src"), 1_234_567_890)
	archive = os.path.join(str(tmp_path), "baton")
	deploy._write_zipapp(staging, archive)
	with open(archive, "rb") as handle:
		assert handle.read(len(deploy.SHEBANG)) == deploy.SHEBANG
	assert os.stat(archive).st_mode & 0o111, "the artifact is not executable"
	with zipfile.ZipFile(archive) as bundle:
		main = bundle.read("__main__.py").decode("utf-8")
	assert main == deploy.MAIN_SOURCE
	assert "baton_work.cli.entry()" in main
	assert "cli.main" not in main


# -- the property, end to end ----------------------------------------------

@pytest.mark.serial
def test_two_real_deployments_agree_on_bytes_and_reported_digest(tmp_path):
	"""The acceptance item as an operator meets it: deploy twice, compare
	the artifact AND the digest the deployer reports."""
	targets = []
	digests = []
	for name in ("first", "second"):
		target = os.path.join(str(tmp_path), name)
		done = subprocess.run([sys.executable, DEPLOYER, target],
		                      capture_output=True, text=True, timeout=180)
		assert done.returncode == 0, done.stderr or done.stdout
		import json as _json
		digests.append(_json.loads(done.stdout)["archive_sha256"])
		targets.append(os.path.join(target, "bin", "baton"))
	assert digests[0] == digests[1], \
		f"the deployer reported two digests: {digests}"
	assert _digest(targets[0]) == digests[0], \
		"the reported digest does not describe the artifact on disk"
	with open(targets[0], "rb") as a, open(targets[1], "rb") as b:
		assert a.read() == b.read(), "two deployments differ byte for byte"
