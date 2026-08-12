#!/usr/bin/env python3
"""Publish a certified Baton release to a destination outside the repository.

A checkout is a workspace: it changes under people who are not watching it.
Teams currently point at `bin/` inside one, which was harmless only while the
repository held nothing but released bytes. This copies a release somewhere
stable instead.

Four rules carry the design, and each exists because its opposite has a failure
mode nobody notices until it matters:

- The human NAMES the version they are installing, and publish refuses unless
  the certified manifests say exactly that. A tool that deploys "whatever the
  manifests happen to hold" cannot be asked for a specific release, which is
  the only question an operator actually has.
- Nothing reaches the destination until the WHOLE payload is preflighted and
  staged. An earlier version filled the final directory as it copied, so a
  missing late file left a visible partial version -- which the immutability
  rule then blocked anyone from repairing.
- A version directory is IMMUTABLE and is never replaced, including when the
  path is an empty directory somebody else made. Replacing a bad deployment is
  a deliberate removal, not a flag: a flag turns "immutable" into "immutable
  unless someone is in a hurry".
- `current` is the only mutable thing here, and moving it IS the release. It is
  swapped by rename through a uniquely owned staging link, so a shipped command
  can never delete an unrelated object it happened to find in the way.

This NEVER builds. It copies bytes that were already certified, which makes a
deployment the last link in the release gate's chain rather than a second,
weaker way to produce artifacts.

Nothing here creates, copies or discovers a config or a SQLite authority. A
deployed tree is inert until a participant supplies `--config`.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# What a consumer runs and reads. NOT what a developer needs: `src/`, `tests/`,
# `tools/`, `work/`, `schema/`, `compat/` and the justfile are absent on
# purpose, and so is `AGENTS.md` -- that is this repository's own policy, not a
# deployed artifact.
#
# `examples/baton.json` IS included, by ruling: a new team needs a config shape
# to copy. It ships only after publish proves it is an inert TEMPLATE -- see
# `_assert_inert_template` -- because a config inside a deployment is a config
# someone will point at.
#
# The release announcement is NOT here: it is named from the version being
# published, so a 1.1 install cannot carry 1.0's announcement.
PAYLOAD = (
	"bin/baton",
	"bin/baton-tui",
	"docs/AGENTS-MAILBOX-PROTO.md",
	"docs/EFFECTIVE-BATON.md",
	"dist/DISTRIBUTION.json",
	"dist/DISTRIBUTION-TUI.json",
	"examples/baton.json",
	"README.md",
	"LICENSE",
)

MANIFESTS = ("dist/DISTRIBUTION.json", "dist/DISTRIBUTION-TUI.json")

RECORD = "DEPLOYMENT.json"

# `major.minor.patch`, the ruled release spelling.
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

EXECUTABLE_MODE = 0o555
FILE_MODE = 0o444
DIRECTORY_MODE = 0o555


class DeployError(Exception):
	"""A refusal a human should read, rather than a traceback."""


# `RENAME_NOREPLACE`, the only primitive that publishes a directory without a
# window. A `lexists` check followed by `os.rename` is cooperative at best: the
# lock excludes another copy of THIS tool, but any process can create the final
# path in between, and POSIX rename then consumes an empty directory and
# reports success over an object this tool did not create.
RENAME_NOREPLACE = 1
_SYS_RENAMEAT2 = {"x86_64": 316, "aarch64": 276, "armv7l": 382, "i686": 353}


def _rename_noreplace(source: str, target: str) -> None:
	"""Publish `source` at `target`, or fail because `target` exists.

	FAILS CLOSED when the platform cannot promise this. A deployment that
	silently degraded to replacing-rename would be exactly the defect this
	replaces, hidden behind a successful exit code."""
	import ctypes
	import ctypes.util
	import platform

	libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
	source_b = os.fsencode(source)
	target_b = os.fsencode(target)
	AT_FDCWD = -100

	call = getattr(libc, "renameat2", None)
	if call is not None:
		result = call(ctypes.c_int(AT_FDCWD), ctypes.c_char_p(source_b),
		              ctypes.c_int(AT_FDCWD), ctypes.c_char_p(target_b),
		              ctypes.c_uint(RENAME_NOREPLACE))
	else:
		number = _SYS_RENAMEAT2.get(platform.machine())
		if number is None:
			raise DeployError(
				f"no atomic no-replace rename on {platform.machine()}; refusing "
				"to publish without it")
		result = libc.syscall(ctypes.c_long(number),
		                      ctypes.c_int(AT_FDCWD), ctypes.c_char_p(source_b),
		                      ctypes.c_int(AT_FDCWD), ctypes.c_char_p(target_b),
		                      ctypes.c_uint(RENAME_NOREPLACE))
	if result == 0:
		return
	code = ctypes.get_errno()
	if code == errno.EEXIST:
		raise DeployError(
			f"{target} already exists and a deployed version is never rewritten "
			"in place. Remove it deliberately if you mean to replace it.")
	if code in (errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
		raise DeployError(
			"this filesystem cannot perform an atomic no-replace publication; "
			"refusing rather than falling back to a rename that would replace "
			f"whatever is at {target}")
	raise DeployError(f"publishing {target} failed: {os.strerror(code)}")


def _remove_owned(path: str) -> None:
	"""Remove a tree this call created, even after it was hardened.

	`_harden` sets every directory to `0555`, so an ordinary `rmtree` cannot
	unlink anything inside them and the whole staging tree survives a failure
	that happens after hardening. Write permission is restored first, deepest
	directories last."""
	if not os.path.lexists(path):
		return
	for current, directories, _files in os.walk(path, topdown=False,
	                                            followlinks=False):
		for name in directories:
			try:
				os.chmod(os.path.join(current, name), 0o700)
			except OSError:
				pass
		try:
			os.chmod(current, 0o700)
		except OSError:
			pass
	try:
		os.chmod(path, 0o700)
	except OSError:
		pass
	shutil.rmtree(path, ignore_errors=True)


def _fsync_tree(root: str) -> None:
	"""Make the whole staged tree durable: files first, then every directory
	deepest-first.

	Syncing only the staging ROOT left `bin`, `docs`, `dist` and `examples`
	entries unsynced -- a root fsync says nothing about entries inside child
	directories -- and the mode changes happened after the file fsyncs, so
	those were unsynced too."""
	for current, _directories, files in os.walk(root, topdown=False):
		for name in files:
			fd = os.open(os.path.join(current, name),
			             os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
			try:
				os.fsync(fd)
			finally:
				os.close(fd)
		_fsync_dir(current)
	_fsync_dir(root)


def release_document(version: str) -> str:
	"""The announcement belonging to THIS release.

	Hardcoding `docs/RELEASE-1.0.0.md` meant a 1.1 publish would carry the
	previous release's announcement, or fail once that file was retired."""
	return os.path.join("docs", f"RELEASE-{version}.md")


def digest(path: str) -> str:
	with _open_regular(path) as handle:
		return hashlib.sha256(handle.read()).hexdigest()


def _open_regular(path: str):
	"""Open a path that must be a REGULAR, non-symlink file.

	`O_NOFOLLOW` refuses a symlink at the final component and the `fstat`
	refuses anything that is not a regular file. Reading through a symlink
	would let a deployed tree describe bytes that live somewhere else, which is
	precisely what a verified deployment must not do."""
	try:
		fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
	except OSError as error:
		if error.errno in (errno.ELOOP, errno.EMLINK):
			raise DeployError(f"{path} is a symlink; refusing") from None
		raise DeployError(f"{path} is unreadable: {error.strerror}") from None
	try:
		if not stat.S_ISREG(os.fstat(fd).st_mode):
			os.close(fd)
			raise DeployError(f"{path} is not a regular file; refusing")
	except DeployError:
		raise
	except Exception:
		os.close(fd)
		raise
	return os.fdopen(fd, "rb")


def _no_symlink_ancestors(path: str, stop: str) -> None:
	"""Refuse a symlinked directory anywhere between `stop` and `path`.

	A regular file reached through a symlinked parent is still a file
	somewhere else; checking only the leaf would miss it."""
	current = os.path.abspath(os.path.dirname(path))
	stop = os.path.abspath(stop)
	while current.startswith(stop) and current != stop:
		if os.path.islink(current):
			raise DeployError(f"{current} is a symlinked directory; refusing")
		current = os.path.dirname(current)


def _assert_inert_template(path: str) -> None:
	"""The example config must be a TEMPLATE, not somebody's live instance.

	It ships so a new team has a shape to copy. What it must never carry is a
	route into a real authority."""
	with _open_regular(path) as handle:
		raw = handle.read()
	try:
		document = json.loads(raw.decode("utf-8"))
	except (ValueError, UnicodeDecodeError):
		raise DeployError(f"{path} is not readable JSON; refusing") from None
	for key in ("sqlite", "database", "authority"):
		if key in document:
			raise DeployError(f"{path} names a live {key}; refusing")
	for root in (document.get("roots") or {}).values():
		if isinstance(root, str) and os.path.isabs(root) and os.path.exists(root):
			raise DeployError(
				f"{path} points at an existing absolute root {root!r}; refusing")


def certified(source: str, version: str) -> dict:
	"""Everything that must be true of the source BEFORE anything is written.

	The gate, not a courtesy check, and it now covers every file the manifests
	ADDRESS -- including the protocol document, which an earlier version copied
	without checking its pin. That left 1.0 binaries pairable with newer
	protocol prose and a `DEPLOYMENT.json` written over the mixture, whose own
	later `verify` would bless it."""
	if not VERSION_RE.match(version or ""):
		raise DeployError(
			f"{version!r} is not a release version; expected major.minor.patch")

	release = protocol = None
	pinned_docs: list[str] = []
	for name in MANIFESTS:
		path = os.path.join(source, name)
		if not os.path.exists(path):
			raise DeployError(f"{name} is missing; nothing certifies this tree")
		with _open_regular(path) as handle:
			manifest = json.loads(handle.read().decode("utf-8"))

		artifact = os.path.join(source, manifest["artifact"])
		if not os.path.exists(artifact):
			raise DeployError(f"{manifest['artifact']} is missing")
		actual = digest(artifact)
		if actual != manifest["artifact_sha256"]:
			raise DeployError(
				f"{manifest['artifact']} does not match {name}\n"
				f"  manifest: {manifest['artifact_sha256']}\n"
				f"  actual:   {actual}\n"
				"  this tree is not certified; build and re-run the release gate")

		if manifest["release_version"] != version:
			raise DeployError(
				f"{name} names release {manifest['release_version']}, not the "
				f"requested {version}")
		release = manifest["release_version"]

		# BOTH protocol versions, COMPARED. The earlier loop overwrote this, so
		# two manifests naming different protocols published quietly.
		if protocol is not None and manifest["protocol_version"] != protocol:
			raise DeployError(
				f"the manifests disagree on the protocol version: "
				f"{protocol} vs {manifest['protocol_version']}")
		protocol = manifest["protocol_version"]

		pinned = manifest.get("protocol_doc")
		if pinned:
			pinned_path = os.path.join(source, pinned)
			if not os.path.exists(pinned_path):
				raise DeployError(f"{pinned} is missing but pinned by {name}")
			actual_doc = digest(pinned_path)
			if actual_doc != manifest["protocol_doc_sha256"]:
				raise DeployError(
					f"{pinned} does not match the hash pinned in {name}\n"
					f"  manifest: {manifest['protocol_doc_sha256']}\n"
					f"  actual:   {actual_doc}")
			pinned_docs.append(pinned)

	payload = list(dict.fromkeys(
		list(PAYLOAD) + [release_document(version)] + pinned_docs))
	for name in payload:
		path = os.path.join(source, name)
		if not os.path.exists(path):
			raise DeployError(f"{name} is missing from {source}")
		_no_symlink_ancestors(path, source)
		with _open_regular(path):
			pass                      # regular, non-symlink, readable
	_assert_inert_template(os.path.join(source, "examples/baton.json"))
	return {"release_version": release, "protocol_version": protocol,
	        "payload": payload}


def _fsync_dir(path: str) -> None:
	fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
	try:
		os.fsync(fd)
	finally:
		os.close(fd)


def _harden(root: str) -> None:
	"""Read-only, deepest first, so a directory is sealed after its contents.

	This does NOT make a deployment tamper-proof: whoever owns the filesystem
	can change a mode and edit anything, and `verify` is what answers that.
	What it stops is accident -- a stray write, an editor saving into a
	deployed tree, a build dropping output there."""
	for current, directories, files in os.walk(root, topdown=False):
		for name in files:
			path = os.path.join(current, name)
			executable = os.path.basename(current) == "bin"
			os.chmod(path, EXECUTABLE_MODE if executable else FILE_MODE)
		for name in directories:
			os.chmod(os.path.join(current, name), DIRECTORY_MODE)
	os.chmod(root, DIRECTORY_MODE)


def publish(source: str, destination: str, version: str) -> str:
	"""Stage the whole release, then move it into place atomically."""
	facts = certified(source, version)
	version_dir = os.path.join(destination, "v" + version)

	os.makedirs(destination, exist_ok=True)
	# An early, friendly refusal. It is NOT what guarantees no-replace -- the
	# publication below does that, atomically, at the moment it matters. This
	# only saves staging a whole release to learn the answer.
	if os.path.lexists(version_dir):
		raise DeployError(
			f"{version_dir} already exists and a deployed version is never "
			"rewritten in place. Remove it deliberately if you mean to "
			"replace it.")

	# CREATED, therefore OWNED. `mkdtemp` makes the directory atomically with a
	# name nobody else holds, so cleanup can never remove somebody else's work
	# -- a pid-derived name can collide after pid reuse, and deleting whatever
	# sat there was the cure being worse than the disease.
	staging = tempfile.mkdtemp(prefix=f".staging-v{version}-", dir=destination)
	try:
		files = {}
		for name in facts["payload"]:
			src = os.path.join(source, name)
			dst = os.path.join(staging, name)
			os.makedirs(os.path.dirname(dst), exist_ok=True)
			with _open_regular(src) as reader:
				data = reader.read()
			with open(dst, "wb") as writer:
				writer.write(data)
				writer.flush()
				os.fsync(writer.fileno())
			files[name] = hashlib.sha256(data).hexdigest()

		# NO TIMESTAMP. A deployed tree is byte-reproducible from the same
		# release, so `verify` is exact and two people deploying one version
		# get identical trees. The filesystem already records when.
		record = {
			"release_version": facts["release_version"],
			"protocol_version": facts["protocol_version"],
			"files": dict(sorted(files.items())),
		}
		with open(os.path.join(staging, RECORD), "w") as handle:
			json.dump(record, handle, indent=2, sort_keys=True)
			handle.write("\n")
			handle.flush()
			os.fsync(handle.fileno())

		problems = verify(staging, expect_modes=False)
		if problems:
			raise DeployError("the staged tree does not verify:\n  "
			                  + "\n  ".join(problems))
		_harden(staging)
		# AFTER hardening, so the mode changes are durable too, and every
		# nested directory -- not just the staging root.
		_fsync_tree(staging)
		_rename_noreplace(staging, version_dir)
		_fsync_dir(destination)
	except BaseException:
		# ONLY the tree this call created, and removable even though hardening
		# has made every directory in it read-only.
		_remove_owned(staging)
		raise
	return version_dir


def _expected_mode(relative: str) -> int:
	"""The mode a deployed entry must carry. Directories and `bin/` leaves are
	executable; everything else is read-only data."""
	if os.path.dirname(relative) == "bin":
		return EXECUTABLE_MODE
	return FILE_MODE


def verify(version_dir: str, *, expect_modes: bool = True) -> list[str]:
	"""Re-hash every deployed file against the record, and check its mode.

	Bytes alone were not enough: changing `README.md` from `0444` to `0644`
	without touching a byte returned no problems at all, and activation would
	then accept a writable tree. The official tamper test changed both, so the
	digest -- not the mode -- was what failed it.

	`expect_modes=False` is for the staged tree, which is deliberately still
	writable while it is being built."""
	root = os.path.abspath(version_dir)
	try:
		info = os.lstat(root)
	except OSError as error:
		return [f"{version_dir}: {error.strerror}"]
	if stat.S_ISLNK(info.st_mode):
		# A symlinked ROOT is not seen by the leaf checks, which stop before
		# examining it -- so `verify` would have happily validated a
		# deployment living somewhere else entirely.
		return [f"{version_dir} is a symlink; refusing to verify through it"]
	if not stat.S_ISDIR(info.st_mode):
		return [f"{version_dir} is not a directory"]
	if expect_modes and stat.S_IMODE(info.st_mode) != DIRECTORY_MODE:
		return [f"{version_dir}: expected mode {DIRECTORY_MODE:o}, "
		        f"found {stat.S_IMODE(info.st_mode):o}"]

	path = os.path.join(version_dir, RECORD)
	if not os.path.exists(path):
		return [f"{RECORD} is missing; this is not a deployed tree"]
	try:
		with _open_regular(path) as handle:
			record = json.loads(handle.read().decode("utf-8"))
	except DeployError as refusal:
		return [str(refusal)]
	problems = []
	for name, expected in sorted(record["files"].items()):
		target = os.path.join(version_dir, name)
		if not os.path.lexists(target):
			problems.append(f"{name}: missing")
			continue
		try:
			_no_symlink_ancestors(target, version_dir)
			actual = digest(target)
		except DeployError as refusal:
			problems.append(f"{name}: {refusal}")
			continue
		if actual != expected:
			problems.append(f"{name}: expected {expected}, found {actual}")
		if expect_modes:
			mode = stat.S_IMODE(os.lstat(target).st_mode)
			wanted = _expected_mode(name)
			if mode != wanted:
				problems.append(
					f"{name}: expected mode {wanted:o}, found {mode:o}")
	# A file nobody recorded is as much a problem as a changed one: it is
	# content in a deployed tree that no release put there.
	if expect_modes:
		mode = stat.S_IMODE(os.lstat(path).st_mode)
		if mode != FILE_MODE:
			problems.append(f"{RECORD}: expected mode {FILE_MODE:o}, found {mode:o}")
	recorded = set(record["files"]) | {RECORD}
	for dirpath, directories, names in os.walk(version_dir):
		if expect_modes:
			for name in directories:
				sub = os.path.join(dirpath, name)
				mode = stat.S_IMODE(os.lstat(sub).st_mode)
				if mode != DIRECTORY_MODE:
					rel = os.path.relpath(sub, version_dir)
					problems.append(
						f"{rel}/: expected mode {DIRECTORY_MODE:o}, found {mode:o}")
		for name in names:
			rel = os.path.relpath(os.path.join(dirpath, name), version_dir)
			if rel not in recorded:
				problems.append(f"{rel}: present but not recorded")
	return problems


def activate(destination: str, version: str) -> str:
	"""Point `<destination>/current` at a deployed version, atomically.

	A symlink replaced by rename: no reader observes a half-switched tree, and
	rolling back is this same call naming the previous version. The staging
	link is uniquely owned, and anything unexpected already sitting at either
	name is REFUSED rather than removed -- a shipped command must not delete
	objects it did not create."""
	version_dir = os.path.join(destination, "v" + version)
	if os.path.islink(version_dir) or not os.path.isdir(version_dir):
		raise DeployError(f"{version_dir} is not a deployed version directory")
	problems = verify(version_dir)
	if problems:
		raise DeployError("refusing to activate a tree that does not verify:\n  "
		                  + "\n  ".join(problems))

	link = os.path.join(destination, "current")
	if os.path.lexists(link) and not os.path.islink(link):
		raise DeployError(
			f"{link} exists and is not a symlink; refusing to replace it")

	staging = os.path.join(destination, f".current-{os.getpid()}")
	if os.path.lexists(staging):
		raise DeployError(f"{staging} already exists; refusing")
	os.symlink("v" + version, staging)
	try:
		os.rename(staging, link)
	except BaseException:
		try:
			os.remove(staging)
		except OSError:
			pass
		raise
	_fsync_dir(destination)
	return link


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(
		prog="deploy",
		description="Publish a certified Baton release outside the repository")
	sub = parser.add_subparsers(dest="command", required=True)

	publish_cmd = sub.add_parser("publish", help="copy a certified release to DESTINATION")
	publish_cmd.add_argument("destination")
	publish_cmd.add_argument("version", help="the release to install, e.g. 1.1.0")
	publish_cmd.add_argument("--source", default=ROOT,
	                         help="release tree to publish (default: this repository)")

	verify_cmd = sub.add_parser("verify", help="re-hash a deployed version directory")
	verify_cmd.add_argument("version_dir")

	activate_cmd = sub.add_parser("activate", help="point DESTINATION/current at a version")
	activate_cmd.add_argument("destination")
	activate_cmd.add_argument("version")

	args = parser.parse_args(argv)
	try:
		if args.command == "publish":
			where = publish(args.source, args.destination, args.version)
			print(json.dumps({"deployed": where}, indent=2))
			return 0
		if args.command == "verify":
			problems = verify(args.version_dir)
			if problems:
				print(json.dumps({"ok": False, "problems": problems}, indent=2))
				return 1
			print(json.dumps({"ok": True}, indent=2))
			return 0
		where = activate(args.destination, args.version)
		print(json.dumps({"current": where, "version": args.version}, indent=2))
		return 0
	except DeployError as refusal:
		print(f"deploy: {refusal}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
