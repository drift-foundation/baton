#!/usr/bin/env python3
"""Publish a certified Baton release to a destination outside the repository.

A checkout is a workspace: it changes under people who are not watching it.
Teams currently point at `bin/` inside one, which was harmless only while the
repository held nothing but released bytes. This copies a release somewhere
stable instead.

Four rules carry the design, and each exists because its opposite has a failure
mode nobody notices until it matters:

- A deployment is an immutable SET, named by the digest of its certified facts.
  Its products are versioned independently -- `baton` and `baton-tui` need not
  carry the same number -- so no single version string could identify what is
  being installed, and the digest does. `publish` prints it; `activate` demands
  it in full. (Superseded: the human used to name the version and publish
  refused unless both manifests said exactly that. The property it protected --
  that an operator can ask for a SPECIFIC thing rather than "whatever the
  manifests happen to hold" -- is what the digest preserves.)
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
import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# WHAT IS PUBLISHED: the candidate `just build` prepared, and nothing else.
#
# The default used to be the repository root, which meant deployment read
# zipapps and templates straight out of a working tree. Two problems, and the
# second is the one that matters: a checkout changes under people who are not
# watching it, so the set that passed `just test` and the set that reached the
# destination could differ by any Git-owned file edited in between. `build/` is
# a snapshot taken at one moment from one tree, and it is the only tree this
# tool reads payload bytes from.
CANDIDATE = os.path.join(ROOT, "build")

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
# The release announcements are NOT here: they are named from each product and
# the version being published, so an install cannot carry a previous release's
# announcement.
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

# EACH MANIFEST PATHNAME IS BOUND TO THE PRODUCT IT MUST DESCRIBE. Trusting
# the `tool` field alone let a mislabelled manifest name the wrong product --
# and two manifests both claiming `baton` collapsed into one dictionary entry,
# so coherence examined one artifact and the set digest identified one of two.
MANIFESTS = {"dist/DISTRIBUTION.json": "baton",
             "dist/DISTRIBUTION-TUI.json": "baton-tui"}

# The attestations each builder emits and this gate therefore REQUIRES. They
# were type-checked when present and absent without complaint, so deleting one
# quietly removed a check -- and a manifest missing an attestation is not a
# supported weaker shape, it is an incomplete one.
REQUIRED_PER_PRODUCT = {"baton": ("source_sha256",),
                        "baton-tui": ("members",)}
REQUIRED_PINS = ("protocol_doc", "protocol_doc_sha256")

# The embedded catalog contract, MIRRORED from `baton_core.products` and kept
# honest by a test that compares the two. The deployer cannot import the core
# -- it certifies distributions, not this repository -- so the contract is
# restated rather than shared, and the test is what stops the restatement from
# drifting.
CATALOG_MEMBER = "baton_core/products.json"
CATALOG_FORMAT = "baton.products"
CATALOG_FORMAT_VERSIONS = (1,)

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


def release_document(tool: str, version: str) -> str:
	"""The announcement belonging to THIS product at THIS version.

	Hardcoding `docs/RELEASE-1.0.0.md` meant a 1.1 publish would carry the
	previous release's announcement, or fail once that file was retired.

	PER PRODUCT now, because a set has no single version to name a note after:
	`docs/RELEASE-baton-1.1.0.md`, `docs/RELEASE-baton-tui-1.4.0.md`. The
	pre-split `docs/RELEASE-1.0.0.md` keeps its name -- it is the history of a
	release that genuinely had one number, and renaming history to match a
	later scheme would make it describe something that never happened.

	NOT YET RULED. Slawomir ruled the version model and the deployment shape;
	note naming was raised and not answered, so this is the implementation's
	choice and is cheap to change."""
	return os.path.join("docs", f"RELEASE-{tool}-{version}.md")


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


def certified(source: str) -> dict:
	"""Everything that must be true of the source BEFORE anything is written.

	The gate, not a courtesy check. It covers every file the manifests ADDRESS
	-- including the protocol document, which an earlier version copied without
	checking its pin. That left 1.0 binaries pairable with newer protocol prose
	and a `DEPLOYMENT.json` written over the mixture, whose own later `verify`
	would bless it.

	NO VERSION ARGUMENT. Products are independently versioned now, so there is
	no single number a human could name that identifies the set: `baton` may be
	1.1.0 while `baton-tui` is 1.4.0. What identifies a set is the digest over
	its certified facts, computed here and returned. The human names THAT at
	activation, having read it from the publish they just performed.

	(Superseded: publish used to take the intended version and refuse unless
	both manifests said exactly it. The rule it protected -- "a tool that
	deploys whatever the manifests happen to hold cannot be asked for a
	specific release" -- survives as the digest: naming a set digest at
	activation is the same question asked in the only terms that remain
	unambiguous.)
	"""
	products: dict[str, dict] = {}
	documents: dict[str, dict] = {}
	protocol = None
	pinned_docs: list[str] = []
	artifacts: dict[str, str] = {}
	for name, expected_tool in sorted(MANIFESTS.items()):
		path = os.path.join(source, name)
		if not os.path.exists(path):
			raise DeployError(f"{name} is missing; nothing certifies this tree")
		manifest = _json_document(path, name)
		_certified_manifest(name, manifest, expected_tool)
		if manifest["tool"] != expected_tool:
			raise DeployError(
				f"{name} describes {manifest['tool']!r}, but this distribution "
				f"expects it to describe {expected_tool!r}")
		documents[name] = manifest

		_safe_relative(manifest["artifact"], f"{name}: artifact")
		if manifest["artifact"] in artifacts:
			raise DeployError(
				f"{name} and {artifacts[manifest['artifact']]} name the same "
				f"artifact {manifest['artifact']}; two products cannot be one file")
		artifacts[manifest["artifact"]] = name
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
		# AND THE ARTIFACT ITSELF IS ASKED. Matching the whole-file digest only
		# proves the manifest describes THESE bytes; every semantic claim above
		# it -- product version, protocol, core API, embedded core -- was taken
		# on trust, so both manifests could carry the same false core identity
		# and certify. The archive carries the catalog and the core members, so
		# the claims are checkable against the thing they claim about.
		_attested(artifact, name, manifest, expected_tool)

		# BOTH protocol versions, COMPARED. The earlier loop overwrote this, so
		# two manifests naming different protocols published quietly.
		if protocol is not None and manifest["protocol_version"] != protocol:
			raise DeployError(
				f"the manifests disagree on the protocol version: "
				f"{protocol} vs {manifest['protocol_version']}")
		protocol = manifest["protocol_version"]

		pinned = manifest.get("protocol_doc")
		if pinned:
			_safe_relative(pinned, f"{name}: protocol_doc")
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

		products[expected_tool] = _product_facts(manifest)

	# COMPLETE BY CONSTRUCTION: every entry of `MANIFESTS` must exist and is
	# keyed by the product it is required to describe, so a set cannot be
	# missing a product or hold two of one. An explicit completeness check here
	# would be unreachable, and unreachable code is a claim nothing can keep.
	_coherent(products)
	notes = [release_document(tool, entry["version"])
	         for tool, entry in sorted(products.items())]
	payload = list(dict.fromkeys(list(PAYLOAD) + notes + pinned_docs))
	digests = {}
	for name in payload:
		path = os.path.join(source, name)
		if not os.path.exists(path):
			raise DeployError(f"{name} is missing from {source}")
		_no_symlink_ancestors(path, source)
		with _open_regular(path) as handle:
			digests[name] = hashlib.sha256(handle.read()).hexdigest()
	_assert_inert_template(os.path.join(source, "examples/baton.json"))
	return {"protocol_version": protocol, "products": products,
	        "payload": payload, "manifests": documents,
	        "set_digest": set_digest(protocol, documents, digests)}


def _unique_pairs(pairs):
	seen = {}
	for key, value in pairs:
		if key in seen:
			raise ValueError(f"duplicate key {key!r}")
		seen[key] = value
	return seen


def _strict_document(path: str, what: str) -> dict:
	"""`_json_document`, refusing duplicate keys.

	For documents whose CONTENT becomes evidence: a record that says two
	different things and is resolved by ordering is not a record.
	"""
	with _open_regular(path) as reader:
		raw = reader.read()
	try:
		document = json.loads(raw.decode("utf-8"),
		                      object_pairs_hook=_unique_pairs)
	except (ValueError, UnicodeDecodeError) as broken:
		raise DeployError(f"{path} is not usable as {what} ({broken})") from None
	if not isinstance(document, dict):
		raise DeployError(f"{path} is not a JSON object")
	return document


def _json_document(path: str, what: str) -> dict:
	"""Read one JSON object, or refuse by name.

	A decode failure used to surface as a traceback from inside the gate. These
	documents are the deployer's TRUST INPUTS: the one thing they must never do
	is fail in a way that looks like a bug in the tool rather than a problem
	with the tree."""
	with _open_regular(path) as handle:
		raw = handle.read()
	try:
		document = json.loads(raw.decode("utf-8"))
	except (ValueError, UnicodeDecodeError) as error:
		raise DeployError(f"{what} is not readable JSON: {error}") from None
	if not isinstance(document, dict):
		raise DeployError(f"{what} is not an object")
	return document


def _require_int(value, where: str) -> int:
	"""An integer, and NOT a bool. `True == 1` in Python, so `protocol_version:
	true` would compare equal to protocol 1 and travel into the set identity as
	a plausible fact."""
	if isinstance(value, bool) or not isinstance(value, int):
		raise DeployError(f"{where} is not an integer: {value!r}")
	return value


def _require_sha(value, where: str) -> str:
	"""Lowercase 64-hex. Anything else is not a digest, and a digest that is
	not one compares unequal to every real digest -- which reads as tampering
	rather than as the malformed document it is."""
	if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
		raise DeployError(f"{where} is not a sha256 digest: {value!r}")
	return value


def _require_semver(value, where: str) -> str:
	if not isinstance(value, str) or not VERSION_RE.match(value):
		raise DeployError(f"{where} is not major.minor.patch: {value!r}")
	return value


def _attested(artifact: str, name: str, manifest: dict, tool: str) -> None:
	"""Ask the ARTIFACT whether the manifest's claims about it are true.

	The whole-file digest proves a manifest describes these bytes. It proves
	nothing about what the manifest SAYS they are: a relabelled product
	version, a different protocol, a false embedded-core identity, all pass a
	digest check untouched, because none of them changes a byte of the archive.
	Both manifests carrying the same false core passed the gate before this.

	The archive carries the catalog it was built from and the core members
	themselves, so every claim is checkable against the thing it claims about.
	A distribution's own artifact is the authority on what it contains.
	"""
	import zipfile

	try:
		with zipfile.ZipFile(artifact) as archive:
			members = {entry: archive.read(entry) for entry in archive.namelist()}
	except (zipfile.BadZipFile, OSError) as error:
		raise DeployError(
			f"{manifest['artifact']} is not a readable zipapp: {error}") from None

	if CATALOG_MEMBER not in members:
		raise DeployError(
			f"{manifest['artifact']} carries no {CATALOG_MEMBER}; it cannot say "
			f"what it is, so {name} cannot be checked against it")
	try:
		catalog = json.loads(members[CATALOG_MEMBER].decode("utf-8"))
	except (ValueError, UnicodeDecodeError) as error:
		raise DeployError(
			f"{manifest['artifact']} carries an unreadable catalog: {error}") from None
	# THE SAME DOCUMENT CONTRACT THE RUNTIME READER ENFORCES. Without this the
	# gate would certify an artifact that refuses to load its own identity: the
	# console inside it would fail at startup on a catalog format it does not
	# understand, having been published as fit to run.
	if not isinstance(catalog, dict):
		raise DeployError(f"{manifest['artifact']}: its catalog is not an object")
	if catalog.get("format") != CATALOG_FORMAT:
		raise DeployError(
			f"{manifest['artifact']} carries a catalog of format "
			f"{catalog.get('format')!r}, which this distribution's own reader "
			f"does not load")
	if catalog.get("format_version") not in CATALOG_FORMAT_VERSIONS:
		raise DeployError(
			f"{manifest['artifact']} carries catalog format version "
			f"{catalog.get('format_version')!r}, which this distribution's own "
			f"reader does not load")
	try:
		entry = catalog["products"][tool]
		claimed = {
			"product_version": entry["version"],
			"requires_core_api": entry["requires_core_api"],
			"artifact": entry["artifact"],
			"protocol_version": catalog["protocol_version"],
			"python_min": catalog["floors"]["python_min"],
			"sqlite_min": catalog["floors"]["sqlite_min"],
			"core_version": catalog["core"]["version"],
			"core_api": catalog["core"]["api_version"],
		}
	except (ValueError, UnicodeDecodeError, KeyError, TypeError) as error:
		raise DeployError(
			f"{manifest['artifact']} carries an unreadable catalog: {error}") from None

	for field in ("product_version", "requires_core_api", "artifact",
	              "protocol_version", "python_min", "sqlite_min"):
		if manifest[field] != claimed[field]:
			raise DeployError(
				f"{name} claims {field}={manifest[field]!r} but "
				f"{manifest['artifact']} carries {claimed[field]!r}")
	core = manifest["embeds_core"]
	if core["version"] != claimed["core_version"] \
			or core["api_version"] != claimed["core_api"]:
		raise DeployError(
			f"{name} claims to embed core {core['version']} API "
			f"{core['api_version']} but {manifest['artifact']} carries "
			f"{claimed['core_version']} API {claimed['core_api']}")

	# THE CORE DIGEST, recomputed the same way the builder computes it: each
	# packaged member's name then its bytes, in sorted name order.
	recomputed = hashlib.sha256()
	for member in sorted(m for m in members if m.startswith("baton_core/")):
		recomputed.update(member.encode("utf-8"))
		recomputed.update(members[member])
	if recomputed.hexdigest() != core["package_sha256"]:
		raise DeployError(
			f"{name} claims embedded core {core['package_sha256']} but "
			f"{manifest['artifact']} contains {recomputed.hexdigest()}")

	source_claim = manifest.get("source_sha256")
	if source_claim is not None:
		impl = members.get("baton_core/_impl.py")
		if impl is None:
			raise DeployError(
				f"{name} pins source_sha256 but {manifest['artifact']} carries "
				f"no baton_core/_impl.py")
		actual = hashlib.sha256(impl).hexdigest()
		if actual != source_claim:
			raise DeployError(
				f"{name} pins source_sha256 {source_claim} but "
				f"{manifest['artifact']} carries {actual}")

	listed = manifest.get("members")
	if listed is not None and sorted(listed) != sorted(members):
		raise DeployError(
			f"{name} lists members that are not what {manifest['artifact']} "
			f"contains")


def _product_facts(manifest: dict) -> dict:
	"""What a manifest says about its product, in the record's shape.

	One definition, used when certifying and again when verifying a deployed
	record: `products` is DERIVED from the manifests, so a record whose summary
	disagrees with the manifests it carries has been edited."""
	return {
		"version": manifest["product_version"],
		"artifact": manifest["artifact"],
		"artifact_sha256": manifest["artifact_sha256"],
		"requires_core_api": manifest["requires_core_api"],
		"embeds_core": dict(manifest["embeds_core"]),
		"protocol_version": manifest["protocol_version"],
	}


def _safe_relative(value: str, where: str) -> None:
	"""A manifest path may only address INSIDE the distribution root.

	Refused rather than normalized, because this string is joined to a root and
	then opened: `/etc/passwd` or `../../elsewhere` arriving at that join is the
	difference between a manifest and an instruction."""
	if not isinstance(value, str) or not value:
		raise DeployError(f"{where} is not a path")
	if value.startswith("/") or value.startswith("~") or "\\" in value:
		raise DeployError(f"{where} must be a relative POSIX path: {value!r}")
	if any(part in ("", ".", "..") for part in value.split("/")):
		raise DeployError(
			f"{where} must have no empty or dotted component: {value!r}")


def _certified_manifest(name: str, manifest, expected_tool: str) -> None:
	"""The shape a manifest must have before any of it is believed.

	Named fields rather than `.get(...)` at the point of use: a missing
	`product_version` reaching `products[tool]` as `None` would publish a set
	that verifies against its own hole."""
	if not isinstance(manifest, dict):
		raise DeployError(f"{name} is not an object")
	required = ("tool", "product_version", "artifact", "artifact_sha256",
	            "protocol_version", "requires_core_api", "embeds_core",
	            "python_min", "sqlite_min")
	missing = [key for key in required if key not in manifest]
	if missing:
		raise DeployError(
			f"{name} is missing {', '.join(missing)}; it was written by an "
			f"older builder that predates independently versioned products")
	# EVERY FIELD TYPED AT THE BOUNDARY. Presence was checked and type was
	# assumed, so a non-string version reached a regex, a non-string digest
	# reached a slice, and a boolean protocol compared equal to protocol 1 --
	# each surfacing as a traceback or as a plausible fact inside the set
	# identity, rather than as a refusal naming the document.
	if not isinstance(manifest["tool"], str) or not manifest["tool"]:
		raise DeployError(f"{name}: tool is not a name")
	_require_semver(manifest["product_version"], f"{name}: product_version")
	_require_sha(manifest["artifact_sha256"], f"{name}: artifact_sha256")
	_require_int(manifest["protocol_version"], f"{name}: protocol_version")
	_require_int(manifest["requires_core_api"], f"{name}: requires_core_api")
	for floor in ("python_min", "sqlite_min"):
		if not isinstance(manifest[floor], str) or not manifest[floor]:
			raise DeployError(f"{name}: {floor} is not a version string")
	core = manifest["embeds_core"]
	if not isinstance(core, dict) or "version" not in core \
			or "package_sha256" not in core or "api_version" not in core:
		raise DeployError(f"{name} does not attest which core it embeds")
	_require_semver(core["version"], f"{name}: embeds_core.version")
	_require_int(core["api_version"], f"{name}: embeds_core.api_version")
	_require_sha(core["package_sha256"], f"{name}: embeds_core.package_sha256")
	# REQUIRED, per product. Both builders emit these and this gate describes
	# them as certified facts, so an absent one is an incomplete manifest
	# rather than a supported weaker shape -- and deleting it used to remove a
	# check without any refusal.
	for field in REQUIRED_PER_PRODUCT.get(expected_tool, ()):
		if field not in manifest:
			raise DeployError(
				f"{name} is missing {field}, which every {expected_tool} manifest "
				f"attests; its builder emits it")
	if "source_sha256" in manifest:
		_require_sha(manifest["source_sha256"], f"{name}: source_sha256")
	# BOTH PINS, REQUIRED. A pinned document with no digest was skipped
	# silently -- a pin that does not pin -- and a manifest with neither field
	# certified a distribution whose protocol document nothing checked.
	missing_pins = [field for field in REQUIRED_PINS if field not in manifest]
	if missing_pins:
		raise DeployError(
			f"{name} is missing {', '.join(missing_pins)}; every manifest pins "
			f"the protocol document it ships with")
	if not isinstance(manifest["protocol_doc"], str) or not manifest["protocol_doc"]:
		raise DeployError(f"{name}: protocol_doc is not a path")
	_require_sha(manifest["protocol_doc_sha256"], f"{name}: protocol_doc_sha256")
	if "members" in manifest and not (
			isinstance(manifest["members"], list)
			and all(isinstance(member, str) for member in manifest["members"])):
		raise DeployError(f"{name}: members is not a list of names")


def _coherent(products: dict) -> None:
	"""The check that independent cadences make necessary.

	Matching version STRINGS never proved anything about compatibility; they
	only proved two files were written in one act. These are the properties
	that actually decide whether a set can be run together, and every one of
	them is now checkable because the manifests attest to the embedded core.
	"""
	if not products:
		raise DeployError("no products are certified in this tree")
	for tool, entry in sorted(products.items()):
		core = entry["embeds_core"]
		if entry["requires_core_api"] != core["api_version"]:
			raise DeployError(
				f"{tool} {entry['version']} requires core API "
				f"{entry['requires_core_api']} but embeds core "
				f"{core['version']} offering API {core['api_version']}")
	cores = {entry["embeds_core"]["package_sha256"] for entry in products.values()}
	if len(cores) > 1:
		detail = ", ".join(
			f"{tool} embeds core {entry['embeds_core']['version']} "
			f"({entry['embeds_core']['package_sha256'][:12]}…)"
			for tool, entry in sorted(products.items()))
		raise DeployError(
			f"the products in this tree embed different cores: {detail}. "
			f"A set is published and activated together, so it ships one core.")


def set_digest(protocol, manifests: dict, payload_digests: dict) -> str:
	"""What NAMES a deployed set: the digest of its whole certified composition.

	THE COMPLETE MANIFESTS AND EVERY PAYLOAD BYTE. An earlier version hashed
	the protocol and a reduced product summary, which left README, the guides,
	the example config, the protocol document, both release notes and every
	manifest field outside the identity -- so a tree that differed in any of
	them landed at the same immutable `set-<digest>` path, and the second
	publish reported it as the same set already being there.

	Digests of the payload rather than its bytes: the identity is over WHAT is
	in the set, and re-reading a hundred megabytes to name it would make the
	name cost as much as the copy.

	Serialized canonically, because a digest over an unsorted document is a
	digest over a whim. It is recomputable from a deployed tree alone, which is
	what lets `verify` check that a directory's name is its own."""
	identity = {"format": "baton.set", "format_version": 1,
	            "protocol_version": protocol,
	            "manifests": manifests, "payload": payload_digests}
	canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"),
	                       ensure_ascii=False).encode("utf-8")
	return hashlib.sha256(canonical).hexdigest()


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


# -- the generation layout ---------------------------------------------------
#
# SUPERSEDES `set-<64 hex>/` as the thing a human navigates. A set digest is
# the only name in the old design that cannot lie -- it is computed from the
# bytes it names -- and it is also unreadable, unguessable and impossible to
# say out loud. The ruling keeps the digest as PROVENANCE and gives humans
# paths built from versions, with every check below existing to stop a
# human-assigned name from lying.
#
#     DEST/app/<product>/<namespace>/<vX.Y.Z>/   one immutable release
#     DEST/app/<product>/<namespace>/latest      relative alias, one component
#     DEST/mailbox/<namespace>/MAILBOX.json      the compatibility handshake
#
# `latest` is for discovery. It is NEVER the path a process runs: CPython's
# `zipimport` reopens the archive BY PATH on every lazy import, so a process
# that kept an alias open could seek offsets from the archive it started with
# into the archive that replaced it. Consumers resolve the alias once and
# execute the exact release.

# The installed directory name of each product. `baton` the tool lives under
# `baton-cli` so the product tree is never confused with the executable.
PRODUCT_DIRS = {"baton": "baton-cli", "baton-tui": "baton-tui"}

PRODUCT_RECORD = "PRODUCT.json"
PRODUCT_FORMAT = "baton.product-release"
PRODUCT_FORMAT_VERSION = 1
ALIAS = "latest"

# Which human act installed a release. Today's three ruled stages produce
# identical bytes, and what keeps their audits separate is that each act is
# RECORDED -- not that one exact version pretends to be two releases.
#
# SUPERSEDED: the gate used to be written into every `PRODUCT.json`, and a
# reinstall by a different act was refused as a different release. That
# reversed the ruling that stage three reports `already_installed` on
# identical bytes. The gate now lives only in the operation record beside the
# tree, and it is validated before anything is mutated: an act nobody defined
# is not something to write down and carry on from.
# ONE GATE. `legacy-import` was removed with the legacy release family: there
# is no act that installs the frozen 1.x pair any more, because that pair is
# not a release this deployer manages. Records already written under the old
# gate name stay valid and readable -- they are historical evidence of acts
# that really happened, and rewriting history to match a later rule is the
# one thing an append-only record must never do.
GATES = ("candidate-deploy",)
HISTORICAL_GATES = ("legacy-import",)

# Held for the duration of one install, INSIDE the validated destination.
LOCK = ".deploy.lock"

# The append-only record of deployment ACTS. Which human gate installed what,
# when, and whether every write was confirmed durable -- evidence about the
# operation, deliberately NOT part of any release's identity.
OPERATIONS = "operations"

MAILBOX_RECORD = "MAILBOX.json"
MAILBOX_FORMAT = "baton.mailbox"
MAILBOX_FORMAT_VERSION = 1

# THERE IS NO LEGACY RELEASE FAMILY. Ruled 2026-08-13, superseding the frozen
# grant that used to live here.
#
# `legacy` was a namespace this table named, holding version directories and a
# `latest` alias like any generation -- and it existed only because the 1.x
# pair's major did not equal the protocol it serves. The correction is that a
# release's major IS its generation, without exception: every release this
# deployer installs lands in `v<protocol>/v<major>.<minor>.<patch>/`.
#
# The frozen 1.x pair is not a release family any more. It sits directly at
# `app/<product>/legacy/bin/<artifact>` -- binaries and nothing else, no
# version directory, no alias, no record -- and this deployer neither installs
# nor describes it. That directory is a leftover, maintained by hand, and
# saying so is more honest than modelling it as a generation whose rules it
# never actually followed.

# Where each payload file goes inside an exact release. The manifest-pinned
# protocol document keeps its basename so its pin still resolves; `conf/` holds
# shipped templates only, never live configuration.
def _installed_layout(tool: str, manifest: dict, version: str) -> dict:
	"""source-relative -> release-relative, for exactly one product."""
	places = {
		manifest["artifact"]: "bin/" + os.path.basename(manifest["artifact"]),
		"docs/AGENTS-MAILBOX-PROTO.md": "doc/AGENTS-MAILBOX-PROTO.md",
		"docs/EFFECTIVE-BATON.md": "doc/EFFECTIVE-BATON.md",
		"README.md": "doc/README.md",
		"LICENSE": "doc/LICENSE",
		release_document(tool, version): "doc/" + os.path.basename(
			release_document(tool, version)),
		"examples/baton.json": "conf/baton.json.example",
		"tmpl/work-basic-1.md": "tmpl/work-basic-1.md",
	}
	return places


def namespace_for(tool: str, version: str, protocol: int) -> str:
	"""The generation directory this release belongs in. ARITHMETIC, always.

	`vN`, where N is both the application major and the protocol version --
	one number, said twice, and refused when the two disagree. There is no
	grant table and no name that escapes this: a release whose major is not
	its protocol has nowhere to live, because "which of these can talk to
	which" would stop being answerable by reading a path.
	"""
	major = int(version.split(".")[0])
	if major != protocol:
		raise DeployError(
			f"{tool} {version} declares protocol {protocol}, so its major "
			f"{major} does not equal its generation. A release's major IS the "
			f"generation it serves: distinct compatibility needs a distinct "
			f"major, and there is no exception to name.")
	return f"v{major}"


def _release_facts(tool: str, manifest: dict, protocol: int,
                   provenance: dict) -> dict:
	"""Everything PRODUCT.json will say, derived from the certified manifest.

	Nothing here is maintained by a human. `products.json` owns the versions,
	the manifest is generated from it, and this is a projection of the manifest
	plus where it was installed -- so the layout cannot become a second version
	owner, which is the defect the catalog was created to end.
	"""
	version = manifest["product_version"]
	namespace = namespace_for(tool, version, protocol)
	facts = {
		"format": PRODUCT_FORMAT,
		"format_version": PRODUCT_FORMAT_VERSION,
		"tool": tool,
		"product_version": version,
		"protocol_version": protocol,
		"namespace": namespace,
		"requires_core_api": manifest["requires_core_api"],
		"embeds_core": manifest["embeds_core"],
		"artifact": "bin/" + os.path.basename(manifest["artifact"]),
		"artifact_sha256": manifest["artifact_sha256"],
		"manifest": manifest,
		"provenance": provenance,
	}
	# NO `legacy_mapping`. It existed to say out loud that application major 1
	# did not mean protocol 1; with the legacy family removed, every installed
	# release's major IS its protocol and the record would be explaining an
	# exception that no longer exists.
	return facts


def install(source: str, destination: str, *,
            gate: str = "candidate-deploy") -> dict:
	"""Install every product of one certified candidate as an exact release.

	The candidate remains the unit that is CERTIFIED -- one core, one protocol,
	manifests attested against the bytes -- and the exact release directory is
	the unit that is PUBLISHED. Both aliases move only after both products are
	installed and verified, so a legacy pair is never half-advanced.

	This never builds, never opens a mailbox, never edits consumer
	configuration and never executes what it installs.
	"""
	if not os.path.isdir(source):
		raise DeployError(
			f"{source} does not exist. `just deploy` publishes the candidate "
			f"`just build` prepares; run the build first, or name another "
			f"distribution with --source.")
	if gate not in GATES:
		raise DeployError(
			f"{gate!r} is not a deployment act this tool performs "
			f"({', '.join(GATES)}); refusing before anything is written")
	facts = certified(source)
	protocol = facts["protocol_version"]
	# ENOUGH TO RECOMPUTE IT. `set_digest` alone was a claim nothing could
	# check from an installed release -- and a recorded fact nothing verifies
	# reads like a guarantee. The manifests and the payload digest map are
	# exactly what `set_digest()` consumes, so `verify_release` recomputes the
	# number rather than believing it.
	# NO GATE IN HERE. R8: recording which human act installed a release made
	# one exact version have two mutually exclusive identities, so the ruled
	# stage three -- `already_installed` on identical bytes -- became a
	# refusal. The act is evidence ABOUT an operation, and it belongs in the
	# append-only operations record beside the tree, not in the immutable
	# equality boundary of a product release.
	provenance = {"set_digest": facts["set_digest"],
	              "protocol_version": protocol,
	              "manifests": facts["manifests"],
	              "payload": {name: digest(os.path.join(source, name))
	                          for name in facts["payload"]}}

	planned = []
	for manifest_path, tool in sorted(MANIFESTS.items()):
		manifest = facts["manifests"][manifest_path]
		record = _release_facts(tool, manifest, protocol, provenance)
		planned.append((tool, record))

	# ONE INSTALL AT A TIME, per destination, and the lock lives INSIDE the
	# destination this call validated -- not at a pathname that might be a
	# link to somewhere else.
	root_fd = _open_root(destination)
	try:
		with _exclusive(root_fd, destination):
			results = []
			for tool, record in planned:
				results.append(_install_release(root_fd, destination, source,
				                                tool, record))
			# BOTH PRODUCTS FIRST. An alias that advanced while its sibling
			# failed to install would leave a pair nobody chose: a new CLI
			# beside the previous console, both looking deployed. An installed
			# release that no alias names is inert, so installing is safe to do
			# first; ADVANCING is what has to be all-or-nothing.
			aliases = []
			try:
				for tool, record in planned:
					generation_dir = os.path.join(destination, "app",
					                              PRODUCT_DIRS[tool],
					                              record["namespace"])
					# DESCENDED FROM THE HELD ROOT, every time: the lock keeps
					# another DEPLOYER out, and it says nothing about a
					# filesystem substitution by anything else.
					fd, held = _descend(root_fd, ["app", PRODUCT_DIRS[tool],
					                              record["namespace"]])
					try:
						aliases.append(_set_alias_at(
							fd, generation_dir,
							"v" + record["product_version"],
							inside=(root_fd, ["app", PRODUCT_DIRS[tool],
							                  record["namespace"]])))
					finally:
						for descriptor in held:
							os.close(descriptor)
			except BaseException:
				# RECOVER ONLY WHERE RECOVERY IS SAFE.
				#
				# If a committed alias could not be confirmed durable, writing
				# again is issuing a second write after the filesystem's
				# durability operation just failed -- which is exactly what
				# this code told itself it would not do, and then did. In that
				# case nothing is rewritten: the observed targets are reported
				# and a human reconciles.
				recovery = _recover_aliases(root_fd, destination, aliases)
				raise DeployFailed(str(sys.exc_info()[1]), recovery) from None
			operation = _record_operation(root_fd, destination, gate,
			                              facts["set_digest"], results, aliases)
	finally:
		os.close(root_fd)
	return {
		"set_digest": facts["set_digest"],
		"protocol_version": protocol,
		"gate": gate,
		"operation": operation["recorded"],
		"operation_durable": operation["durable"],
		"operation_problem": operation["problem"],
		"releases": results,
		"aliases": aliases,
	}


# WHAT CONTAINMENT CAN AND CANNOT PROMISE.
#
# Everything below resolves inside the destination without following links:
# each component is opened `O_NOFOLLOW | O_DIRECTORY` from its parent's
# descriptor, publication happens through those descriptors, and each write is
# preceded by a re-walk from the destination root that refuses if the
# directory it arrives at is not the one being held.
#
# THAT IS NOT THE SAME AS "nothing can make this write outside the
# destination", and this module previously implied it was. A directory
# descriptor follows an INODE. A process running as the same user can move the
# directory out of the destination between any check and the commit that
# follows it, and the write lands wherever that inode now is. Another check
# moves the race closer to the rename; it does not close it, and no POSIX
# primitive pins a directory to a path.
#
# THE BOUNDARY, APPROVED BY SLAWOMIR ON 2026-08-13 as the cooperative
# single-operator model. What the code enforces and the tests pin:
#
#   REFUSED   a symlink or non-directory anywhere in the destination path,
#             pre-existing or planted, at any depth
#   REFUSED   a directory that is no longer reachable inside the destination
#             at the moment of the last check before a commit
#   REFUSED   a second deployment against the same destination, by lock
#   OUT OF SCOPE, DELIBERATELY  a concurrent same-UID process relocating a
#             directory this operation already validated, in the interval
#             between that last check and the commit
#
# The last line is APPROVED SCOPE, not a solved problem. It is not prevented
# and this module does not claim to prevent it: an actor who can do that can
# equally well delete the destination outright. What is ruled is that a
# deployment tool run by one operator, on a machine whose Baton processes are
# all the same user, does not carry the cost of defending against it.
_RESOLVE_BENEATH = 0x08
_RESOLVE_NO_SYMLINKS = 0x04


def _openat2_beneath(name: str, dir_fd: int) -> int | None:
	"""Open `name` under `dir_fd`, refusing to escape, when the kernel offers
	it. Returns None where `openat2` is unavailable, and the caller falls back
	to component-wise `O_NOFOLLOW` -- which refuses the same links, and which
	is what this ran on before.

	`RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS` makes the KERNEL enforce that the
	resolution stays under the descriptor. It still cannot pin an inode to a
	path, which is why the paragraph above says what it says.
	"""
	import ctypes
	import struct

	libc = ctypes.CDLL(None, use_errno=True)
	if not hasattr(libc, "syscall"):
		return None
	how = struct.pack("QQQ", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, 0,
	                  _RESOLVE_BENEATH | _RESOLVE_NO_SYMLINKS)
	buffer = ctypes.create_string_buffer(how)
	result = libc.syscall(ctypes.c_long(437), ctypes.c_int(dir_fd),
	                      ctypes.c_char_p(os.fsencode(name)),
	                      ctypes.byref(buffer), ctypes.c_size_t(len(how)))
	if result >= 0:
		return int(result)
	code = ctypes.get_errno()
	if code in (errno.ENOSYS, errno.EINVAL, errno.EPERM):
		return None
	raise OSError(code, os.strerror(code), name)


def _open_root(destination: str) -> int:
	"""The destination itself, opened without following anything.

	R13. The install lock used to be created through the lexical destination
	BEFORE the confinement check ran, so a symlinked DEST received a real file
	outside the tree that was named -- briefly, and only briefly because a
	`finally` removed it. A crash in that interval left it there. Nothing is
	created through a pathname until this has answered.
	"""
	root = os.path.abspath(destination)
	if os.path.islink(root):
		raise DeployError(
			f"{root} is a symlink; a deployment root is a real directory, and "
			f"following one would install outside the destination named")
	os.makedirs(root, exist_ok=True)
	try:
		return os.open(root, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
	except OSError as exc:
		raise DeployError(f"{root} is not a usable deployment root "
		                  f"({exc.strerror})") from None


def _descend(root_fd: int, components: list[str]) -> tuple:
	"""Walk further in from a validated descriptor, one component at a time."""
	fd = root_fd
	held = []
	try:
		for name in components:
			try:
				os.mkdir(name, dir_fd=fd)
			except FileExistsError:
				pass
			try:
				# The kernel enforces "beneath, no symlinks" where it can; the
				# fallback refuses the same objects one component at a time.
				nxt = _openat2_beneath(name, fd)
				if nxt is None:
					nxt = os.open(name,
					              os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
					              dir_fd=fd)
			except OSError as exc:
				raise DeployError(
					f"{'/'.join(components)}: {name!r} is a symlink or not a "
					f"directory ({exc.strerror}); refusing to install through "
					f"it") from None
			held.append(nxt)
			fd = nxt
		return fd, held
	except BaseException:
		for descriptor in held:
			os.close(descriptor)
		raise


def _confined(destination: str, components: list[str]) -> str:
	"""Walk into the destination one component at a time, refusing to leave it.

	R1. Paths were built as strings and `os.makedirs` opened whatever the
	ancestors happened to be. A symlink at `DEST/app` -- planted, or left over
	from somebody's convenience -- was FOLLOWED, so an install reported paths
	lexically under DEST and wrote both products somewhere else entirely.

	Each component is created or opened with `O_NOFOLLOW | O_DIRECTORY` from
	the descriptor of its parent, so nothing in the chain can be a link and no
	component is resolved twice. The returned path is `/proc/self/fd/N`, which
	names THE DIRECTORY THIS CALL VALIDATED rather than a string that can be
	re-resolved into a different one between two operations.
	"""
	root_fd = _open_root(destination)
	try:
		fd, held = _descend(root_fd, components)
	except BaseException:
		os.close(root_fd)
		raise
	return fd, [root_fd] + held


def _still_inside(root_fd: int, components: list[str], fd: int,
                  expected: str) -> None:
	"""Is the directory this call holds STILL inside the destination?

	A descriptor follows an INODE, not a name. Comparing the descriptor with
	the lexical pathname is not enough: if somebody moves the whole product
	directory out of the destination and leaves a symlink behind, the lexical
	path resolves THROUGH that link to the very inode being held -- identical,
	and outside. So the check re-walks from the destination root without
	following anything, and asks whether the directory it arrives at is this
	one.
	"""
	walked = root_fd
	opened = []
	try:
		for name in components:
			try:
				walked = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
				                 dir_fd=walked)
			except OSError as exc:
				raise DeployError(
					f"{expected} is no longer reachable inside the destination "
					f"({exc.strerror}); it was moved or replaced, and nothing "
					f"further was written") from None
			opened.append(walked)
		here = os.fstat(walked)
		mine = os.fstat(fd)
		if (here.st_dev, here.st_ino) != (mine.st_dev, mine.st_ino):
			raise DeployError(
				f"{expected} is no longer the directory this operation "
				f"validated; it was moved or replaced, and writing through the "
				f"descriptor would put bytes outside the destination that was "
				f"named")
	finally:
		for descriptor in opened:
			os.close(descriptor)


def _at(fd: int, *parts: str) -> str:
	"""A path THROUGH a held descriptor. Linux-only, like `renameat2` above:
	`/proc/self/fd/N` follows the directory this process opened, so an
	ancestor swapped after validation cannot redirect a later operation."""
	return os.path.join(f"/proc/self/fd/{fd}", *parts)


class DeployFailed(DeployError):
	"""A deployment that failed AND what recovery did about it.

	R24: the recovery loop ignored every alias's durability, used a bare
	`unlink` with no directory fsync for the previous-absent case, and
	swallowed every error -- so an operator saw only "the second alias failed"
	while the first might still be advanced, or rolled back without confirmed
	durability. The original failure stays primary; what recovery observed is
	attached to it rather than hidden behind it.
	"""

	def __init__(self, failure: str, recovery: list):
		self.failure = failure
		self.recovery = recovery
		unresolved = [item for item in recovery
		              if item["state"] != "restored" or not item["durable"]]
		detail = "\n  ".join(
			f"{item['alias']}: now names {item['observed']!r}; recovery "
			f"{item['state']}"
			+ ("" if item["durable"] else ", NOT confirmed durable")
			+ (f" ({item['problem']})" if item["problem"] else "")
			for item in recovery)
		super().__init__(
			failure
			+ ("\n\nRecovery:\n  " + detail if recovery else "")
			+ ("\n\nSOME ALIASES ARE NOT WHERE THIS COMMAND FOUND THEM. "
			   "Reconcile with `deploy.py resolve` before anything is run "
			   "from them." if unresolved else ""))


def _recover_aliases(root_fd: int, destination: str, aliases: list) -> list:
	"""Put back what advanced, and report exactly what happened to each.

	An alias that committed without confirmed durability is NOT rewritten: a
	second write after a failed durability call is not a repair. Its observed
	target is reported instead, which is the thing an operator has to act on.
	"""
	recovery = []
	for done in reversed(aliases):
		generation = os.path.dirname(done["alias"])
		components = os.path.relpath(generation, destination).split(os.sep)
		item = {"alias": done["alias"], "target": done["target"],
		        "previous": done["previous"], "state": "left", "durable": True,
		        "problem": None, "observed": done["target"]}
		if not done["durable"]:
			item["problem"] = ("the advance was committed without confirmed "
			                   "durability; nothing was written over it")
			item["durable"] = False
			recovery.append(item)
			continue
		try:
			fd, held = _descend(root_fd, components)
			try:
				if done["previous"] is None:
					# ATOMIC-ENOUGH AND DURABLE: the previous-absent case used
					# a bare unlink with no directory sync, so "there is no
					# alias" was itself an unconfirmed claim.
					os.unlink(ALIAS, dir_fd=fd)
					try:
						_fsync_dir(_at(fd))
					except OSError:
						item["durable"] = False
					item["state"] = "restored"
					item["observed"] = None
				else:
					back = _set_alias_at(fd, generation, done["previous"],
					                     inside=(root_fd, components))
					item["state"] = "restored"
					item["durable"] = back["durable"]
					item["observed"] = back["target"]
			finally:
				for descriptor in held:
					os.close(descriptor)
		except (OSError, DeployError) as failure:
			item["state"] = "failed"
			item["problem"] = str(failure)
			item["durable"] = False
		recovery.append(item)
	return recovery


def _record_operation(root_fd: int, destination: str, gate: str,
                      set_digest_value: str, releases: list,
                      aliases: list) -> dict:
	"""Publish what this act did, as ONE immutable document beside the tree.

	SUPERSEDED: this appended a line to `OPERATIONS.jsonl`. A single `os.write`
	is not promised to write a whole line, a first-time create was never
	fsynced at the directory, and a truncated tail is not something a later
	append can repair -- so the evidence that keeps the three gates separate
	could quietly become unparseable. Each act now gets its own file, written
	to a unique name, fsynced, and published with an atomic no-replace rename.

	It reports its own committed/durable outcome. Evidence that failed to be
	written is not a reason to undo product and alias writes that succeeded --
	but it is absolutely a reason for the command not to claim success.
	"""
	entry = {
		"format": "baton.deployment-operation",
		"format_version": 1,
		"gate": gate,
		"set_digest": set_digest_value,
		"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
		"releases": [{"tool": item["tool"], "version": item["version"],
		              "namespace": item["namespace"], "state": item["state"],
		              "durable": item["durable"]} for item in releases],
		"aliases": [{"alias": os.path.relpath(item["alias"], destination),
		             "target": item["target"], "previous": item["previous"],
		             "durable": item["durable"]} for item in aliases],
	}
	# NO `recovered` KEY. It carried the provenance of a candidate assembled
	# from the running installation, and both the recovery tool and the import
	# gate that produced one are gone. Records already written with it remain
	# exactly as they were.
	rendered = (json.dumps(entry, indent=2, sort_keys=True) + "\n").encode("utf-8")
	# EVERY FAILURE FROM HERE IS AN OUTCOME. R23: `mkstemp` sat outside the
	# guarded block, and `_descend`'s `mkdir` failure escaped too, so an
	# ordinary ENOSPC while writing EVIDENCE raised after both releases and
	# both aliases had committed -- reporting the deployment as a crash when
	# what actually failed was the note about it.
	try:
		return _write_operation(root_fd, destination, rendered)
	except (OSError, DeployError) as failure:
		return {"recorded": None, "durable": False, "problem": str(failure)}


def _write_operation(root_fd: int, destination: str, rendered: bytes) -> dict:
	operations_fd, held = _descend(root_fd, [OPERATIONS])
	try:
		through = _at(operations_fd)
		handle, staging = tempfile.mkstemp(prefix=".operation-", dir=through)
		# UNIQUE BY CONSTRUCTION: a name built from the UTC second, the digest
		# and the gate collides when the same act repeats inside one second --
		# which is exactly what an idempotent re-deployment does.
		entry = json.loads(rendered.decode("utf-8"))
		unique = os.path.basename(staging)[len(".operation-"):]
		name = (f"{entry['utc'].replace(':', '')}-{entry['set_digest'][:12]}"
		        f"-{entry['gate']}-{unique}.json")
		try:
			with os.fdopen(handle, "wb") as writer:
				# WRITTEN COMPLETELY: `os.write` may write less than it is
				# given; a buffered writer loops, and flush + fsync is what
				# makes the bytes real before the rename.
				writer.write(rendered)
				writer.flush()
				os.fsync(writer.fileno())
			os.chmod(staging, FILE_MODE)
			_rename_noreplace(staging, os.path.join(through, name))
		except BaseException:
			if os.path.lexists(staging):
				os.unlink(staging)
			raise
		durable = True
		try:
			_fsync_dir(through)
			# AND THE PARENT: the first act creates `operations/` itself, and
			# syncing only the child says nothing about the entry naming it.
			_fsync_dir(_at(root_fd))
		except OSError:
			durable = False
		return {"recorded": os.path.join(destination, OPERATIONS, name),
		        "durable": durable, "problem": None}
	finally:
		for descriptor in held:
			os.close(descriptor)


@contextlib.contextmanager
def _exclusive(root_fd: int, destination: str):
	"""One install at a time against one destination.

	`O_CREAT | O_EXCL` on a lock beside the destination, so a second process
	is refused rather than allowed to interleave its per-product updates with
	this one's. A stale lock is a legible refusal a human clears, not
	something this tool decides to break: the alternative is two deployments
	believing they each own the tree.
	"""
	lock = os.path.join(os.path.abspath(destination), LOCK)
	try:
		fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644,
		             dir_fd=root_fd)
	except FileExistsError:
		raise DeployError(
			f"{lock} exists, so another deployment holds this destination. If "
			f"nothing is running, remove it deliberately -- two installs "
			f"interleaving their alias updates can leave a pair neither of "
			f"them asked for.") from None
	try:
		os.write(fd, f"{os.getpid()}\n".encode())
		os.close(fd)
		yield
	finally:
		try:
			os.unlink(LOCK, dir_fd=root_fd)
		except OSError:
			pass


def _install_release(root_fd: int, destination: str, source: str, tool: str,
                     record: dict) -> dict:
	"""One exact, immutable release directory, or an idempotent no-op.

	A collision is not automatically an error: publishing the same certified
	candidate twice must be safe. It is an error only if what is already there
	DIFFERS -- and then it refuses without touching a byte, because distinct
	bytes are a distinct version, not a second copy of this one.
	"""
	version = record["product_version"]
	release_dir = os.path.join(destination, "app", PRODUCT_DIRS[tool],
	                           record["namespace"], "v" + version)
	places = _installed_layout(tool, record["manifest"], version)

	staged_files = {}
	for relative, installed in sorted(places.items()):
		with _open_regular(os.path.join(source, relative)) as reader:
			data = reader.read()
		staged_files[installed] = {"sha256": hashlib.sha256(data).hexdigest(),
		                           "mode": _expected_mode(installed),
		                           "bytes": data}
	if record["artifact_sha256"] != staged_files[record["artifact"]]["sha256"]:
		raise DeployError(
			f"{tool} {version}: the artifact does not match its manifest digest")

	document = dict(record)
	document["files"] = {name: {"sha256": facts["sha256"], "mode": facts["mode"]}
	                     for name, facts in sorted(staged_files.items())}
	rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"

	# CONFINED FROM HERE ON. Every path below is reached through descriptors
	# this call opened and checked, never through a string somebody else can
	# re-resolve.
	generation_fd, held = _descend(root_fd, ["app", PRODUCT_DIRS[tool],
	                                         record["namespace"]])
	try:
		return _install_confined(generation_fd, release_dir, tool, version,
		                         record, staged_files, rendered, root_fd)
	finally:
		for descriptor in held:
			os.close(descriptor)


def _install_confined(generation_fd: int, release_dir: str, tool: str,
                      version: str, record: dict, staged_files: dict,
                      rendered: str, root_fd: int | None = None) -> dict:
	generation_dir = _at(generation_fd)
	if os.path.lexists(_at(generation_fd, "v" + version)):
		return _already_installed(_at(generation_fd, "v" + version), tool,
		                          version, rendered, reported=release_dir)

	try:
		staging = tempfile.mkdtemp(prefix=f".staging-{PRODUCT_DIRS[tool]}-",
		                           dir=generation_dir)
	except OSError as exc:
		# The validated directory is gone or unusable -- somebody replaced or
		# removed it after this call opened it. The write did NOT follow them
		# anywhere: it went to the descriptor, which no longer has a path.
		raise DeployError(
			f"the destination changed underneath this install ({exc.strerror}); "
			f"nothing was written") from None
	try:
		for installed, facts in sorted(staged_files.items()):
			target = os.path.join(staging, installed)
			os.makedirs(os.path.dirname(target), exist_ok=True)
			with open(target, "wb") as writer:
				writer.write(facts["bytes"])
				writer.flush()
				os.fsync(writer.fileno())
		with open(os.path.join(staging, PRODUCT_RECORD), "w") as handle:
			handle.write(rendered)
			handle.flush()
			os.fsync(handle.fileno())
		problems = verify_release(staging, expect_modes=False,
		                          expect_location=False)
		if problems:
			raise DeployError(f"the staged {tool} release does not verify:\n  "
			                  + "\n  ".join(problems))
		_harden(staging)
		_fsync_tree(staging)
		if root_fd is not None:
			_still_inside(root_fd,
			              ["app", PRODUCT_DIRS[tool], record["namespace"]],
			              generation_fd, os.path.dirname(release_dir))
		_rename_noreplace(staging, os.path.join(generation_dir, "v" + version))
	except BaseException:
		_remove_owned(staging)
		raise
	# COMMITTED. R9: the directory fsync used to sit inside the block above,
	# so a durability failure raised while the immutable release was ALREADY
	# at its final pathname -- the same contradiction the aliases were
	# corrected for. The release stays; the durability is reported.
	durable = True
	try:
		_fsync_dir(generation_dir)
	except OSError:
		durable = False
	# AT THE PUBLISHED PATH, where the location checks mean something. The
	# staged verification could not answer them: staging is deliberately named
	# something nobody else holds. Checked through the held descriptor, and
	# then again at the reported path, so the two must be the same directory.
	problems = verify_release(_at(generation_fd, "v" + version),
	                          expect_location=False)
	problems += verify_release(release_dir)
	if problems:
		raise DeployError(f"{release_dir} does not verify after publication:\n  "
		                  + "\n  ".join(problems))
	return {"tool": tool, "version": version, "namespace": record["namespace"],
	        "path": release_dir, "state": "installed", "durable": durable}


def _already_installed(release_dir: str, tool: str, version: str,
                       rendered: str, reported: str | None = None) -> dict:
	"""An exact release that is already there: identical, or refused.

	`release_dir` may be reached through a held descriptor, whose `/proc` path
	says nothing about the layout -- so the location checks run against the
	pathname a human would type, and the content checks against the descriptor
	that cannot be re-resolved.
	"""
	problems = verify_release(release_dir, expect_location=False)
	if reported:
		problems += verify_release(reported)
	if problems:
		raise DeployError(
			f"{release_dir} already exists and does not verify:\n  "
			+ "\n  ".join(problems)
			+ "\nRefusing to touch it. An installed release is immutable; "
			  "investigate rather than reinstall.")
	existing = _json_document(os.path.join(release_dir, PRODUCT_RECORD),
	                          "the installed product record")
	if json.dumps(existing, indent=2, sort_keys=True) + "\n" != rendered:
		raise DeployError(
			f"{release_dir} already exists and describes a DIFFERENT "
			f"{tool} {version}. Distinct bytes are a distinct version: this "
			f"candidate is not a second {version}. Nothing was changed.")
	# RECONFIRM ON RETRY. A previous install may have committed this release
	# without confirming it durable; repeating the command is how a human
	# resolves that, so the retry syncs the directory rather than returning
	# early with nothing done.
	durable = True
	try:
		_fsync_dir(os.path.dirname(release_dir.rstrip("/")))
	except OSError:
		durable = False
	where = reported or release_dir
	return {"tool": tool, "version": version,
	        "namespace": os.path.basename(os.path.dirname(where)),
	        "path": where, "state": "already_installed", "durable": durable}


def verify_release(release_dir: str, *, expect_modes: bool = True,
                   expect_location: bool = True) -> list[str]:
	"""Re-hash an exact release against its own record, and check that its
	name, namespace, version and protocol all say the same thing.

	`expect_location` is False only while a release is still in staging, where
	the directory is deliberately named something nobody else holds. Every
	location check is re-run at the published path by `install`'s callers and
	by `verify-release`."""
	problems = []
	record_path = os.path.join(release_dir, PRODUCT_RECORD)
	try:
		record = _json_document(record_path, "the product record")
	except DeployError as refusal:
		return [str(refusal)]
	for field, expected in (("format", PRODUCT_FORMAT),
	                        ("format_version", PRODUCT_FORMAT_VERSION)):
		if record.get(field) != expected:
			return [f"{record_path}: {field} is {record.get(field)!r}, not "
			        f"{expected!r}"]
	tool = record.get("tool")
	if tool not in PRODUCT_DIRS:
		return [f"{record_path}: names an unknown product {tool!r}"]
	version = _require_semver(record.get("product_version"),
	                          f"{record_path} product_version")
	protocol = _require_int(record.get("protocol_version"),
	                        f"{record_path} protocol_version")
	namespace = record.get("namespace")

	# THE NAME MUST NOT LIE. This is the check that pays for using paths a
	# human can read instead of a digest that cannot be wrong.
	try:
		derived = namespace_for(tool, version, protocol)
	except DeployError as refusal:
		problems.append(str(refusal))
		derived = None
	if derived is not None and namespace != derived:
		problems.append(f"{record_path}: namespace {namespace!r} is not the "
		                f"{derived!r} this release belongs in")
	if expect_location:
		if os.path.basename(release_dir.rstrip("/")) != "v" + version:
			problems.append(f"{release_dir}: directory name does not match "
			                f"product_version {version}")
		parent = os.path.basename(os.path.dirname(release_dir.rstrip("/")))
		if derived is not None and parent != derived:
			problems.append(f"{release_dir}: sits in {parent!r}, but this "
			                f"release belongs in {derived!r}")
		grandparent = os.path.basename(
			os.path.dirname(os.path.dirname(release_dir.rstrip("/"))))
		if grandparent != PRODUCT_DIRS.get(tool):
			problems.append(f"{release_dir}: sits under {grandparent!r}, but "
			                f"{tool} installs under {PRODUCT_DIRS.get(tool)!r}")
	if "legacy_mapping" in record:
		problems.append(f"{record_path}: carries `legacy_mapping`, which was "
		                f"removed with the legacy release family; a record "
		                f"explaining an exception that no longer exists is a "
		                f"record describing a layout this deployer does not "
		                f"produce")

	# THE WHOLE PROJECTION, reconstructed. Version, protocol and the artifact
	# digest were compared and everything else was believed -- so an installed
	# record could name a different core, a different required API or a
	# different candidate and still be reported as verified.
	manifest = record.get("manifest")
	provenance = record.get("provenance")
	if isinstance(manifest, dict) and isinstance(provenance, dict):
		try:
			expected = _release_facts(tool, manifest, protocol, provenance)
			for field in sorted(expected):
				if record.get(field) != expected[field]:
					problems.append(
						f"{record_path}: {field} is not what this manifest "
						f"projects")
		except DeployError as refusal:
			problems.append(str(refusal))
		problems += _provenance_problems(record_path, provenance, tool,
		                                 manifest, protocol)
	else:
		problems.append(f"{record_path}: carries no manifest and provenance to "
		                f"check itself against")

	files = record.get("files")
	if not isinstance(files, dict) or not files:
		return problems + [f"{record_path}: records no files"]
	for name, entry in sorted(files.items()):
		# SHAPE FIRST. A record is a trust document; walking one that is not
		# the shape this code expects produced an AttributeError traceback
		# instead of a refusal a human could act on.
		if not isinstance(name, str):
			return problems + [f"{record_path}: a file entry is not a name"]
		_safe_relative(name, f"{record_path} files")
		if not isinstance(entry, dict):
			return problems + [f"{record_path}: {name} is not described by an "
			                   f"object"]
		if set(entry) != {"sha256", "mode"}:
			return problems + [f"{record_path}: {name} describes "
			                   f"{sorted(entry)}, not sha256 and mode"]
		_require_sha(entry["sha256"], f"{record_path} {name} sha256")
		if not isinstance(entry["mode"], int) or isinstance(entry["mode"], bool) \
				or not 0 <= entry["mode"] <= 0o7777:
			return problems + [f"{record_path}: {name} records no usable mode"]
	present = set()
	if expect_modes:
		# THE RECORD AND THE DIRECTORIES TOO. Only the recorded leaves were
		# checked, so the document granting all this trust -- and every
		# directory holding it -- could be left writable without complaint.
		record_mode = stat.S_IMODE(os.lstat(record_path).st_mode)
		if record_mode != FILE_MODE:
			problems.append(f"{PRODUCT_RECORD}: expected mode {FILE_MODE:o}, "
			                f"found {record_mode:o}")
		own = stat.S_IMODE(os.stat(release_dir).st_mode)
		if own != DIRECTORY_MODE:
			problems.append(f"{release_dir}: expected mode {DIRECTORY_MODE:o}, "
			                f"found {own:o}")
	for current, directories, names in os.walk(release_dir):
		for name in directories:
			if os.path.islink(os.path.join(current, name)):
				problems.append(f"{os.path.join(current, name)}: is a symlink")
				continue
			if expect_modes:
				mode = stat.S_IMODE(os.lstat(os.path.join(current, name)).st_mode)
				if mode != DIRECTORY_MODE:
					problems.append(
						f"{os.path.relpath(os.path.join(current, name), release_dir)}"
						f": expected mode {DIRECTORY_MODE:o}, found {mode:o}")
		for name in names:
			path = os.path.join(current, name)
			relative = os.path.relpath(path, release_dir)
			if relative == PRODUCT_RECORD:
				continue
			present.add(relative)
	for extra in sorted(present - set(files)):
		problems.append(f"{extra}: is in the release and in no record")
	for relative in sorted(set(files) - present):
		problems.append(f"{relative}: is recorded and missing")
	for relative in sorted(set(files) & present):
		expected = files[relative]
		path = os.path.join(release_dir, relative)
		if os.path.islink(path):
			problems.append(f"{relative}: is a symlink")
			continue
		try:
			actual = digest(path)
		except DeployError as refusal:
			problems.append(str(refusal))
			continue
		if actual != expected.get("sha256"):
			problems.append(f"{relative}: expected sha256 "
			                f"{expected.get('sha256')}, found {actual}")
		if expect_modes:
			mode = stat.S_IMODE(os.lstat(path).st_mode)
			if mode != expected.get("mode"):
				problems.append(f"{relative}: expected mode "
				                f"{expected.get('mode'):o}, found {mode:o}")
	artifact = record.get("artifact")
	if artifact in files and files[artifact].get("sha256") != \
			record.get("artifact_sha256"):
		problems.append(f"{record_path}: artifact_sha256 disagrees with the "
		                f"recorded digest of {artifact}")
	manifest = record.get("manifest")
	if not isinstance(manifest, dict) or \
			manifest.get("product_version") != version or \
			manifest.get("protocol_version") != protocol or \
			manifest.get("artifact_sha256") != record.get("artifact_sha256"):
		problems.append(f"{record_path}: the carried manifest disagrees with "
		                f"the release it describes")
	return problems


def _provenance_problems(record_path: str, provenance: dict, tool: str,
                         manifest: dict, protocol: int) -> list[str]:
	"""Recompute the candidate identity this release claims to come from."""
	problems = []
	if set(provenance) != {"set_digest", "protocol_version", "manifests",
	                       "payload"}:
		return [f"{record_path}: provenance describes {sorted(provenance)}, "
		        f"which is not what this build records"]
	manifests = provenance["manifests"]
	payload = provenance["payload"]
	if not isinstance(manifests, dict) or set(manifests) != set(MANIFESTS):
		return problems + [f"{record_path}: provenance carries the wrong "
		                   f"manifests"]
	# The payload a candidate certifies is the generic list PLUS the release
	# note each product names from its own version -- derived here from the
	# carried manifests, so the map cannot quietly gain or lose an entry.
	expected_payload = set(PAYLOAD) | {
		release_document(named, manifests[path]["product_version"])
		for path, named in MANIFESTS.items()}
	if not isinstance(payload, dict) or set(payload) != expected_payload:
		return problems + [f"{record_path}: provenance carries the wrong "
		                   f"payload map"]
	for name, value in sorted(payload.items()):
		_require_sha(value, f"{record_path} provenance payload {name}")
	mine = [path for path, named in MANIFESTS.items() if named == tool]
	if manifests.get(mine[0]) != manifest:
		problems.append(f"{record_path}: the carried manifest is not the one "
		                f"in this release's own provenance")
	if provenance["protocol_version"] != protocol:
		problems.append(f"{record_path}: provenance says protocol "
		                f"{provenance['protocol_version']}, the release says "
		                f"{protocol}")
	recomputed = set_digest(provenance["protocol_version"], manifests, payload)
	if recomputed != provenance["set_digest"]:
		problems.append(f"{record_path}: provenance names candidate "
		                f"{provenance['set_digest'][:12]}… but its own facts "
		                f"compute {recomputed[:12]}…")
	return problems


def set_alias(generation_dir: str, target: str) -> dict:
	"""The standalone command's entry: resolve the path, then do the confined
	work. `install()` never comes through here -- it holds descriptors already
	and passes them straight to `_set_alias_at`."""
	generation_dir = os.path.abspath(generation_dir.rstrip("/"))
	parent = os.path.dirname(generation_dir)
	name = os.path.basename(generation_dir)
	parent_fd = os.open(parent, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
	try:
		try:
			generation_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
			                        dir_fd=parent_fd)
		except OSError as exc:
			raise DeployError(f"{generation_dir} is not a generation directory "
			                  f"({exc.strerror})") from None
		try:
			return _set_alias_at(generation_fd, generation_dir, target)
		finally:
			os.close(generation_fd)
	finally:
		os.close(parent_fd)


def _set_alias_at(generation_fd: int, generation_dir: str, target: str, *,
                  inside: tuple | None = None) -> dict:
	"""Point `<generation>/latest` at an exact release, atomically.

	The alias is a RELATIVE symlink of exactly one component, inside its own
	generation directory, and it is replaced by `rename` rather than
	`unlink`+`symlink` -- the latter has a window in which `latest` does not
	exist, and unlike the candidate's brief absence that one is avoidable.
	Rollback is this same call naming the previous release, which is still
	installed.
	"""
	# ONE CHECK, not two. An earlier version rejected non-component targets
	# and then separately rejected non-`vX.Y.Z` ones -- and the second caught
	# every case the first did, so breaking the first changed nothing and no
	# test could see it. A guard nothing can fail is not a guard.
	if not target.startswith("v") or not VERSION_RE.match(target[1:]):
		raise DeployError(
			f"{target!r} is not an exact release name. `latest` names one "
			f"vX.Y.Z directory inside its own generation -- never a path, "
			f"never another alias, never a range.")
	# EVERYTHING BELOW GOES THROUGH THE DESCRIPTOR. R17: the alias was
	# validated and written through a lexical `DEST/app/.../<namespace>`
	# string, so a directory swapped for a symlink between the release
	# installs and the alias write was followed -- `install()` succeeded, the
	# alias landed outside the destination, and the report printed the DEST
	# path it had never used.
	# Still inside the destination this operation was given -- re-walked from
	# its root, following nothing.
	if inside is not None:
		_still_inside(inside[0], inside[1], generation_fd, generation_dir)
	through = _at(generation_fd)
	release_dir = os.path.join(through, target)
	reported = os.path.join(generation_dir, target)
	if os.path.islink(release_dir) or not os.path.isdir(release_dir):
		raise DeployError(
			f"{reported} is not an installed release directory; refusing to "
			f"point an alias at it")
	problems = verify_release(release_dir, expect_location=False)
	if problems:
		raise DeployError(f"{reported} does not verify:\n  "
		                  + "\n  ".join(problems)
		                  + "\nThe alias was not changed.")
	record = _json_document(os.path.join(release_dir, PRODUCT_RECORD),
	                        "the product record")
	if record.get("namespace") != os.path.basename(generation_dir.rstrip("/")):
		raise DeployError(
			f"{reported} belongs to {record.get('namespace')!r}; an alias "
			f"never crosses generations")

	alias_path = os.path.join(through, ALIAS)
	if os.path.lexists(alias_path) and not os.path.islink(alias_path):
		raise DeployError(
			f"{os.path.join(generation_dir, ALIAS)} exists and is not a "
			f"symlink; refusing to replace an object this tool did not create")
	previous = os.readlink(alias_path) if os.path.islink(alias_path) else None
	handle, staging = tempfile.mkstemp(prefix=f".{ALIAS}-", dir=through)
	os.close(handle)
	os.unlink(staging)
	try:
		os.symlink(target, staging)
		os.rename(staging, alias_path)
	except BaseException:
		if os.path.lexists(staging):
			os.unlink(staging)
		raise
	# COMMITTED HERE. The rename either happened or it did not, and from this
	# line on the alias names `target`.
	#
	# The durability call is reported, never used to decide what happened. It
	# used to raise -- so a failed fsync surfaced as "the alias did not move"
	# while the alias HAD moved, and any rollback written afterwards would be
	# a second write on a filesystem that just failed one. What is honest is
	# to adopt what the pathname now names and say the durability is
	# unconfirmed.
	durable = True
	try:
		_fsync_dir(through)
	except OSError:
		durable = False
	return {"alias": os.path.join(generation_dir, ALIAS), "target": target,
	        "previous": previous, "resolved": reported, "durable": durable,
	        "execute": os.path.join(reported, record["artifact"])}


def resolve_alias(generation_dir: str) -> str:
	"""What a consumer must do ONCE, at launch: read the alias, validate it,
	and then execute the exact path it names -- never the alias itself."""
	alias_path = os.path.join(generation_dir, ALIAS)
	if not os.path.islink(alias_path):
		raise DeployError(f"{alias_path} is not a discovery alias")
	target = os.readlink(alias_path)
	if target != os.path.basename(target) or target.startswith("."):
		raise DeployError(f"{alias_path} points at {target!r}, which is not a "
		                  f"single component inside its generation")
	release_dir = os.path.join(generation_dir, target)
	if not os.path.isdir(release_dir):
		raise DeployError(f"{alias_path} is dangling: {target!r} is not there")
	problems = verify_release(release_dir)
	if problems:
		raise DeployError(f"{release_dir} does not verify:\n  "
		                  + "\n  ".join(problems))
	return release_dir


def mailbox_identity(mailbox_dir: str, protocol: int, *,
                     namespace: str | None = None) -> str:
	"""Write the compatibility handshake beside a mailbox.

	Deliberately NOT part of publication and deliberately not a mailbox
	operation: it writes one document beside an authority, opens no database,
	and is used at the move destination.

	HOW THE AUTHORITY ITSELF TRAVELS depends on the move, and this deployment's
	was ruled specifically: a full stop, an offline `mv` of the config and the
	SQLite files on one filesystem, then a restart -- with a hand-written
	`MOVED` pointer left in the old directory that nothing follows
	automatically. The core's audited move ceremony remains for moves that
	need it; it is not what this cutover uses, and this document must not
	teach the procedure the ruling replaced.
	"""
	if namespace is None:
		namespace = f"v{protocol}"
	# FORMAT, NAMESPACE, PROTOCOL. Nothing else.
	#
	# SUPERSEDED 2026-08-13: this also wrote a `legacy_mapping` naming exact
	# applications and versions, and startup checked membership in it. Baton
	# has no per-application mailbox grant: which exact releases may be
	# installed is a deployment-certification question, and the core API is a
	# product/core embedding contract. A mailbox is asked one thing -- what
	# protocol it is -- and this document answers that.
	document = {
		"format": MAILBOX_FORMAT,
		"format_version": MAILBOX_FORMAT_VERSION,
		"protocol_version": protocol,
		"namespace": namespace,
	}
	path = os.path.join(mailbox_dir, MAILBOX_RECORD)
	rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
	if os.path.lexists(path):
		# IDEMPOTENT for identical bytes. An interrupted publication must be
		# safe to repeat: refusing a retry that would write exactly what is
		# already there turns a durability hiccup into a manual repair.
		if not os.path.islink(path) and os.path.isfile(path) and \
				open(path, encoding="utf-8").read() == rendered:
			# The bytes are right; what a retry adds is the durability the
			# interrupted publication could not confirm, so it syncs rather
			# than returning early having done nothing.
			durable = True
			try:
				_fsync_dir(mailbox_dir)
			except OSError:
				durable = False
			return {"written": path, "state": "already_written",
			        "durable": durable}
		raise DeployError(f"{path} already exists and differs; refusing to "
		                  f"rewrite a mailbox identity")
	os.makedirs(mailbox_dir, exist_ok=True)
	handle, staging = tempfile.mkstemp(prefix=f".{MAILBOX_RECORD}-",
	                                   dir=mailbox_dir)
	try:
		with os.fdopen(handle, "w") as writer:
			writer.write(rendered)
			writer.flush()
			os.fsync(writer.fileno())
		os.chmod(staging, FILE_MODE)
		_rename_noreplace(staging, path)
	except BaseException:
		if os.path.lexists(staging):
			os.unlink(staging)
		raise
	# Committed above; durability is reported, not used to decide what
	# happened -- and a retry with identical bytes is accepted, so an
	# unconfirmed publication has an obvious next step.
	durable = True
	try:
		_fsync_dir(mailbox_dir)
	except OSError:
		durable = False
	return {"written": path, "state": "written", "durable": durable}


# SET PUBLICATION IS RETIRED. `publish()` wrote `set-<digest>/` trees and
# `activate()` pointed one global `current` at them. Both are superseded by
# exact per-product releases and generation-scoped aliases: two products that
# version independently cannot share one activation pointer, and a 64-hex
# directory is a name no human can carry between two terminals.
#
# `verify()` below still READS a published set. Sets exist on disk, somebody
# may need to check one, and retiring their ability to do that is not an
# upgrade -- but nothing writes that shape any more.


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
		record = _json_document(path, RECORD)
	except DeployError as refusal:
		return [str(refusal)]
	if not isinstance(record.get("files"), dict):
		return [f"{RECORD} has no file record; this is not a deployed tree"]
	# EVERY RECORDED PATH IS CONFINED, BEFORE ANYTHING IS JOINED OR OPENED.
	# The keys of `files` were taken straight to `os.path.join` against the
	# deployment root, so a record naming `../outside-secret` with that file's
	# digest verified successfully -- the record became an instruction to read
	# outside the tree, and an incomplete deployment could be made to verify by
	# substituting files that were never in it.
	#
	# Both record versions, and before the identity computation: a bad path
	# must not be reachable by any later step, and `_authentic` returning a
	# problem does not stop the file loop below.
	confinement = []
	for key, expected in record["files"].items():
		try:
			_safe_relative(key, f"{RECORD}: files entry")
			_require_sha(expected, f"{RECORD}: digest for {key!r}")
		except DeployError as refusal:
			confinement.append(str(refusal))
	if confinement:
		return confinement
	# LEGACY RECORDS STAY VERIFIABLE, read-only. A version-1 record was written
	# before products were versioned independently; its file digests and modes
	# mean exactly what they meant then, so they are still checked. What this
	# tool will not do is WRITE that shape again.
	#
	# RECOGNIZED BY ITS ACTUAL SHAPE, not by the absence of a key. Defaulting a
	# missing `record_version` to 1 meant a version-2 record whose version key
	# was deleted was read as legacy -- and legacy has no identity to check, so
	# deleting one key turned every check below off.
	version = record.get("record_version")
	if version is None:
		if any(key in record for key in ("set_digest", "products", "manifests")):
			return [f"{RECORD} carries version-2 fields but no record_version; "
			        f"refusing to read it as a legacy record"]
		version = 1
	if version not in (1, 2):
		return [f"{RECORD} is record version {version!r}, which this tool "
		        f"does not read"]
	problems = list(_authentic(version, record, root, expect_name=expect_modes))
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


def _authentic(version: int, record: dict, root: str, *, expect_name: bool):
	"""Does this tree's RECORDED IDENTITY hold, and is its name its own?

	A version-2 record names the set it belongs to. Without this, a valid tree
	copied or renamed under any other 64-hex name still verified and could be
	activated by that false digest -- the digest identified the composition and
	nothing checked that the directory agreed.

	`expect_name` is off while staging, whose basename is a temporary the
	publication has not yet given its real name. The INTERNAL identity is
	checked either way, which is what makes the staged tree worth verifying at
	all.

	Version 1 has no identity to check. That is a fact about the old record,
	not a gap: it is verified against its own file digests, exactly as it
	always was.
	"""
	if version == 1:
		return
	digest_value = record.get("set_digest")
	if not isinstance(digest_value, str) or not re.fullmatch(r"[0-9a-f]{64}",
	                                                         digest_value):
		yield f"{RECORD}: set_digest is not a digest"
		return
	manifests = record.get("manifests")
	products = record.get("products")
	if not isinstance(manifests, dict) or not isinstance(products, dict):
		yield f"{RECORD}: a version-2 record must carry manifests and products"
		return
	if not isinstance(record.get("protocol_version"), int):
		yield f"{RECORD}: protocol_version is not an integer"
		return
	recomputed = set_digest(record["protocol_version"], manifests, record["files"])
	if recomputed != digest_value:
		yield (f"{RECORD}: the recorded set_digest does not describe this "
		       f"record\n  recorded:   {digest_value}\n  recomputed: {recomputed}")
		return
	# `products` is a DERIVED summary, so it is checked against the manifests
	# it summarizes rather than trusted. Without this, editing it changed
	# nothing the identity covered.
	try:
		expected = {document["tool"]: _product_facts(document)
		            for document in manifests.values()}
	except (KeyError, TypeError):
		yield f"{RECORD}: the recorded manifests are not manifests"
		return
	if products != expected:
		yield (f"{RECORD}: the recorded products do not summarize the recorded "
		       f"manifests")
		return
	if expect_name:
		name = os.path.basename(root.rstrip("/"))
		if name != "set-" + digest_value:
			yield (f"{name}: this tree is set {digest_value}; a deployed set "
			       f"directory is named for the set it contains")


def _deployed_products(where: str) -> dict:
	"""What a deployed tree says it contains, for the human reading the output.

	Reads the record rather than re-deriving: this is a report, and a report
	that recomputes what it is reporting on can disagree with `verify`."""
	try:
		with _open_regular(os.path.join(where, RECORD)) as handle:
			record = json.loads(handle.read().decode("utf-8"))
	except (DeployError, OSError, ValueError):
		return {}
	if record.get("record_version", 1) == 1:
		# A version-1 tree has one release version and no product detail.
		return {"release_version": record.get("release_version")}
	return {tool: entry.get("version")
	        for tool, entry in sorted((record.get("products") or {}).items())}


def _report(result: dict) -> dict:
	"""What a human needs to read after a deployment: where the bytes went,
	what the aliases now name, which generation each release serves, and the
	set digest that ties them to one certified candidate."""
	return {
		"set_digest": result["set_digest"],
		"protocol_version": result["protocol_version"],
		"gate": result["gate"],
		"operation_record": result["operation"],
		"operation_problem": result["operation_problem"],
		# EVERY COMMITTED WRITE SAYS WHETHER IT IS DURABLE. `set_alias` and
		# `_install_release` knew; the report dropped it, so `just deploy`
		# printed an ordinary success and the operator never learned that a
		# durability call had failed.
		# INCLUDING THE EVIDENCE. A deployment whose act was never recorded is
		# not a successful deployment: the record is the mechanism that keeps
		# import and candidate deployment separate audits.
		"durable": (all(item["durable"] for item in
		                result["releases"] + result["aliases"])
		            and result["operation_durable"]),
		"releases": [
			{"tool": release["tool"], "version": release["version"],
			 "namespace": release["namespace"], "path": release["path"],
			 "state": release["state"], "durable": release["durable"],
			 "generation": (f"{release['namespace']} = application major "
			                f"= protocol {result['protocol_version']}")}
			for release in result["releases"]],
		"aliases": [
			{"alias": alias["alias"], "target": alias["target"],
			 "previous": alias["previous"], "durable": alias["durable"],
			 # THE EXACT PATH A CONSUMER RUNS. Printed beside the alias so
			 # nobody has to derive it, and so nothing is tempted to put the
			 # alias itself in a configuration file.
			 "execute": alias["execute"]}
			for alias in result["aliases"]],
		"note": ("`latest` is for discovery only. Resolve it once and execute "
		         "the exact release path; a running zipapp must never hold an "
		         "alias open."),
		"durability_note": (
			"every write below is committed; `durable: false` means this "
			"process could not confirm it survives a power cut. Nothing was "
			"rewritten to fix that -- a second write after a failed durability "
			"call is not a repair. Re-run the command to reconfirm."),
	}


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(
		prog="deploy",
		description="Install a certified Baton release outside the repository")
	sub = parser.add_subparsers(dest="command", required=True)

	publish_cmd = sub.add_parser(
		"publish", help="install each certified product as an exact release")
	publish_cmd.add_argument("destination")
	publish_cmd.add_argument("--source", default=CANDIDATE,
	                         help="candidate distribution to publish "
	                              "(default: build/, prepared by `just build`)")

	verify_cmd = sub.add_parser("verify", help="re-hash a deployed set directory")
	verify_cmd.add_argument("set_dir")

	release_cmd = sub.add_parser(
		"verify-release", help="re-hash one exact product release directory")
	release_cmd.add_argument("release_dir")

	alias_cmd = sub.add_parser(
		"alias", help="point <generation>/latest at an exact release")
	alias_cmd.add_argument("generation_dir")
	alias_cmd.add_argument("target", help="the exact release, e.g. v1.1.0")

	resolve_cmd = sub.add_parser(
		"resolve", help="print the exact release <generation>/latest names")
	resolve_cmd.add_argument("generation_dir")

	identity_cmd = sub.add_parser(
		"mailbox-identity", help="write MAILBOX.json beside a mailbox")
	identity_cmd.add_argument("mailbox_dir")
	identity_cmd.add_argument("--protocol", type=int, required=True)

	activate_cmd = sub.add_parser(
		"activate", help="SUPERSEDED by exact releases and discovery aliases")
	activate_cmd.add_argument("destination")
	activate_cmd.add_argument("set_digest", nargs="?")

	args = parser.parse_args(argv)
	try:
		if args.command == "publish":
			report = _report(install(args.source, args.destination))
			print(json.dumps(report, indent=2, sort_keys=True))
			return 0 if report["durable"] else 3
		if args.command == "verify":
			problems = verify(args.set_dir)
			if problems:
				print(json.dumps({"ok": False, "problems": problems}, indent=2))
				return 1
			print(json.dumps({"ok": True, "products": _deployed_products(args.set_dir)},
			                 indent=2, sort_keys=True))
			return 0
		if args.command == "verify-release":
			problems = verify_release(args.release_dir)
			if problems:
				print(json.dumps({"ok": False, "problems": problems}, indent=2))
				return 1
			record = _json_document(
				os.path.join(args.release_dir, PRODUCT_RECORD), "the record")
			print(json.dumps({"ok": True, "tool": record["tool"],
			                  "product_version": record["product_version"],
			                  "protocol_version": record["protocol_version"],
			                  "namespace": record["namespace"]},
			                 indent=2, sort_keys=True))
			return 0
		if args.command == "alias":
			moved = set_alias(args.generation_dir, args.target)
			print(json.dumps(moved, indent=2, sort_keys=True))
			return 0 if moved["durable"] else 3
		if args.command == "resolve":
			release_dir = resolve_alias(args.generation_dir)
			record = _json_document(os.path.join(release_dir, PRODUCT_RECORD),
			                        "the record")
			# THE EXACT PATH, printed for a consumer to record and execute.
			print(json.dumps(
				{"release": release_dir,
				 "execute": os.path.join(release_dir, record["artifact"]),
				 "product_version": record["product_version"],
				 "protocol_version": record["protocol_version"]},
				indent=2, sort_keys=True))
			return 0
		if args.command == "mailbox-identity":
			written = mailbox_identity(args.mailbox_dir, args.protocol)
			print(json.dumps(written, indent=2, sort_keys=True))
			# UNCONFIRMED DURABILITY IS NOT A SUCCESS. The document is there;
			# whether it survives a power cut is not known, and the exit code
			# says so rather than leaving that in a field nobody reads.
			return 0 if written["durable"] else 3
		raise DeployError(
			"`activate` is superseded. There is no global `current`: each "
			"product has an immutable exact release and a generation-scoped "
			"`latest` alias, and consumers execute the resolved exact path. "
			"Use `deploy.py alias <generation-dir> vX.Y.Z` to change what "
			"`latest` names, and `deploy.py resolve <generation-dir>` to read "
			"the exact path to run.")
	except DeployError as refusal:
		print(f"deploy: {refusal}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
