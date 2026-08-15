#!/usr/bin/env python3
"""Prepare the WHOLE release candidate under `build/`: never the checkout.

WHERE THE CANDIDATE GOES, and why it is not the checkout. Installing a
finished set back over `bin/baton` and `bin/baton-tui` made every successful
build a production cutover: teams were told to run the repository executables
and the shared event bridge names one by absolute path, so the bytes reached
live consumers the moment a build succeeded — before `just deploy` had a
chance to be the safety boundary it was written to be. A running process could
also hold modules from the previous zipapp while the next process read the
replacement, which is a mixed-version window nobody asked for.

So `just build` writes a disposable, git-ignored `build/` candidate and the
checkout is left alone. `build/` is a COMPLETE distribution root: both zipapps,
both manifests, every manifest-pinned document, the generic payload, and the
per-product release notes. Deployment publishes from it and reads payload
bytes from nowhere else — otherwise a Git-owned template could change between
`just test` and `just deploy`, and the deployed set would not be the set that
passed the gate.

The source tree stays the maintained owner of those templates. `build/` is a
generated snapshot and is safe to delete wholesale.

Slawomir superseded the two-command human workflow. `baton` and `baton-tui`
are independently versioned products, but they are built from ONE catalog and
they embed ONE core, and the deployer refuses a set whose products disagree
about either. Two commands made that coherence the human's job to remember
between them; one command makes it the build's.

THE FAILURE THIS EXISTS TO PREVENT. Building each product straight into the
repository meant a failure in the second left the first already replaced: a
half-refreshed release tree, with a new CLI beside an old console, both looking
finished. Whether that tree then certifies is a matter of luck -- the products
would embed different cores, so it does not, but "the next gate happens to
catch it" is not a build guarantee.

So: PREPARE EVERYTHING IN A SCRATCH ROOT, verify the complete set there, and
only then install. Nothing touches the release tree until every product has
been built successfully.

HOW ATOMIC IT IS, STATED HONESTLY. SUPERSEDED: this used to replace the payload
leaves inside a visible `build/`, one `os.replace` at a time, and said out loud
that several of them were not one transaction. That honesty was not a
guarantee. An injected failure at the fourth replace produced a candidate
holding a new CLI beside an old console -- every file intact, the set a
mixture -- at exactly the path `deploy` and the gates read.

So the candidate is prepared OUTSIDE the `build/` pathname and published by
renaming a directory. The visible state is the complete previous candidate, the
complete new one, or nothing at all. `build/` is briefly ABSENT while the old
candidate is retired and the new one is moved in, and that is the trade taken
deliberately: absence fails closed -- deploy and the gates say "run the build
first" -- while a mixture is the one state nothing downstream can detect.

WHAT MAY BE DELETED. Publication removes the tree it retires, so it has to know
that tree is its own. Refusing links and non-directories was not enough: an
ordinary directory holding somebody's notes satisfied `isdir` and was deleted
while this module claimed the old candidate had been "resolved and checked".
Every published candidate now carries an ownership record naming exactly what
it holds, and an existing root is retired only when that record is present,
well formed, and matches the directory exactly. Anything else is somebody
else's and is refused with its bytes untouched.

This NEVER deploys. Deployment copies certified bytes and is a separate act.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.path.insert(0, HERE)
import build_zipapp                        # noqa: E402  (sibling tool)
import build_tui                           # noqa: E402

# What one complete release set consists of. Named rather than discovered: a
# build that installed "whatever it produced" could not tell a missing product
# from a product nobody asked for.
PRODUCTS = (
	("baton", build_zipapp, "dist/DISTRIBUTION.json"),
	("baton-tui", build_tui, "dist/DISTRIBUTION-TUI.json"),
)

# The disposable candidate root. Ignored by Git, deletable wholesale, and the
# only thing a build writes.
CANDIDATE = os.path.join(ROOT, "build")

# Git-owned payload the candidate SNAPSHOTS. The source tree remains the
# maintained owner; taking a copy at build time is what makes `build/` a
# complete distribution root, and what stops a template edited after `just
# test` from reaching a deployment that never saw it.
#
# The protocol document is absent because both builders already copy it: it is
# hash-pinned by the manifests, so it travels with the product that pins it.
SNAPSHOT = (
	"docs/EFFECTIVE-BATON.md",
	"examples/baton.json",
	"README.md",
	"LICENSE",
	# WS-6 M6: the numbered dossier-template instruction files are
	# exact-release ASSETS shipped beside bin/doc/conf — never embedded
	# in a zipapp, never importlib resources.
	"tmpl/work-basic-1.md",
)


# THE OWNERSHIP RECORD, and what it authorizes.
#
# Publication retires whatever sits at the candidate path and then removes it
# RECURSIVELY. Refusing links and non-directories was not enough: an ordinary
# directory somebody had been keeping notes in satisfied `isdir` and was
# deleted, while the module claimed the old candidate had been "resolved and
# checked". A check that does not distinguish this build system's output from
# a stranger's directory cannot authorize `rmtree`.
#
# So every candidate this tool publishes carries a record naming exactly what
# it contains, and nothing is retired unless that record is present, well
# formed, and matches the directory EXACTLY -- no missing entries, no extra
# ones, no links anywhere. An unmarked directory is somebody else's; a marked
# one holding a file the record does not name has had something put in it,
# and deleting it would take that with it.
#
# FORMAT 2 RECORDS BYTES AND TYPE. Version 1 recorded pathnames only, and a
# recorded `README.md` replaced by a FIFO -- or by somebody's own text -- was
# neither an extra name nor a missing one, so nothing could see it and both
# were authorized for deletion. Every entry now carries its SHA-256 and its
# mode, and every one of them is recomputed before anything is removed.
#
# Every field here is CHECKED. Declining to record a fact because an
# unverified fact would mislead was the wrong answer: the answer is to verify
# it.
OWNERSHIP = ".baton-candidate.json"
OWNERSHIP_FORMAT = "baton.release-candidate"
OWNERSHIP_FORMAT_VERSION = 2


class BuildError(Exception):
	"""A refusal a human should read, rather than a traceback."""


def prepare(scratch: str) -> dict:
	"""Build every product into `scratch`, snapshot the payload, return the
	manifests.

	One catalog, read by both builders, so the set is coherent by construction
	rather than by the human running two commands in the right order.
	"""
	manifests = {}
	for tool, builder, manifest_path in PRODUCTS:
		manifest = builder.build(scratch)
		if manifest["tool"] != tool:
			raise BuildError(
				f"{builder.__name__} produced a manifest for "
				f"{manifest['tool']!r}, not {tool!r}")
		manifests[manifest_path] = manifest
	_coherent(manifests)
	_snapshot(scratch, manifests)
	return manifests


def _snapshot(scratch: str, manifests: dict) -> None:
	"""Copy the Git-owned payload into the candidate.

	A candidate that carried only the zipapps would leave deployment reading
	templates from the checkout, and a template edited between `just test` and
	`just deploy` would then ship without ever having been in the tree that
	passed the gate. Everything the deployed set contains is snapshotted here,
	at one moment, from one tree."""
	for relative in SNAPSHOT:
		source = os.path.join(ROOT, relative)
		if not os.path.isfile(source):
			raise BuildError(f"the payload file {relative} is missing from {ROOT}")
		target = os.path.join(scratch, relative)
		os.makedirs(os.path.dirname(target), exist_ok=True)
		shutil.copyfile(source, target)
	# The per-product release notes, named from the versions just built. A
	# missing note is a refusal HERE rather than at publication: the build is
	# where a human can still write it.
	for manifest in manifests.values():
		relative = os.path.join(
			"docs", f"RELEASE-{manifest['tool']}-{manifest['product_version']}.md")
		source = os.path.join(ROOT, relative)
		if not os.path.isfile(source):
			raise BuildError(
				f"{relative} is missing; {manifest['tool']} "
				f"{manifest['product_version']} has no release note to ship")
		target = os.path.join(scratch, relative)
		os.makedirs(os.path.dirname(target), exist_ok=True)
		shutil.copyfile(source, target)


def _coherent(manifests: dict) -> None:
	"""The set-level facts, checked HERE so a build cannot hand the deployer a
	set it must refuse.

	The deployer checks these too, and deliberately: it certifies distributions
	it did not build. What this adds is that the failure is reported by the
	thing that caused it, at the moment it can still be fixed by rebuilding.
	"""
	cores = {path: manifest["embeds_core"]["package_sha256"]
	         for path, manifest in manifests.items()}
	if len(set(cores.values())) > 1:
		raise BuildError(
			f"the products were built from different cores: {cores}. One build "
			f"reads one catalog, so this means the tree changed mid-build.")
	protocols = {manifest["protocol_version"] for manifest in manifests.values()}
	if len(protocols) > 1:
		raise BuildError(f"the products disagree on the protocol: {protocols}")
	# REQUIRED VERSUS PROVIDED, per product. This is the check that decides
	# whether a set can be RUN, and it was missing: the module claimed the
	# build could not hand the deployer a set it must refuse, and a manifest
	# requiring API 4 while embedding API 3 installed cleanly and was then
	# refused at publication. A claim a gate does not make is worse than no
	# claim, because it stops anyone looking.
	for path, manifest in sorted(manifests.items()):
		offered = manifest["embeds_core"]["api_version"]
		if manifest["requires_core_api"] != offered:
			raise BuildError(
				f"{manifest['tool']} requires core API "
				f"{manifest['requires_core_api']} but embeds core "
				f"{manifest['embeds_core']['version']} offering API {offered} "
				f"({path})")


def _open_regular(path: str):
	"""Open a leaf for reading, following nothing and blocking on nothing.

	`O_NOFOLLOW` because a link is not this build's file, and `O_NONBLOCK`
	because a FIFO sitting at a recorded pathname would otherwise make the
	validator wait forever for a writer that never comes -- a check that hangs
	is a check nobody runs. The type is confirmed on the DESCRIPTOR, so what is
	read is what was checked.
	"""
	descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
	if not stat.S_ISREG(os.fstat(descriptor).st_mode):
		os.close(descriptor)
		raise BuildError(
			f"{path} is not a regular file; this is not material a build wrote")
	return descriptor


def _digest(path: str) -> str:
	descriptor = _open_regular(path)
	try:
		digest = hashlib.sha256()
		while True:
			chunk = os.read(descriptor, 1 << 20)
			if not chunk:
				return digest.hexdigest()
			digest.update(chunk)
	finally:
		os.close(descriptor)


def _facts(root: str) -> dict:
	"""What is actually in `root`: every leaf, its digest and its mode.

	Refuses symlinks -- `os.walk` merely declines to descend into a linked
	directory -- and refuses anything that is not a regular file. A FIFO, a
	socket or a device node at a recorded pathname is not something a build
	wrote, and the previous version of this could not tell: it compared
	NAMES, so a recorded `README.md` replaced by a FIFO, or by a human's own
	bytes, was authorized for recursive deletion.
	"""
	facts = {}
	for base, directories, files in os.walk(root):
		for name in directories:
			path = os.path.join(base, name)
			if os.path.islink(path):
				raise BuildError(
					f"{os.path.relpath(path, root)} is a symlink; this is not a "
					f"candidate this build produced")
		for name in files:
			path = os.path.join(base, name)
			relative = os.path.relpath(path, root)
			mode = os.lstat(path).st_mode
			if stat.S_ISLNK(mode):
				raise BuildError(
					f"{relative} is a symlink; this is not a candidate this "
					f"build produced")
			if not stat.S_ISREG(mode):
				raise BuildError(
					f"{relative} is not a regular file; this is not a candidate "
					f"this build produced")
			facts[relative] = {"sha256": _digest(path),
			                   "mode": stat.S_IMODE(mode)}
	return facts


def _stamp(staging: str) -> None:
	"""Record what this candidate contains, so a later build may retire it.

	FORMAT 2 records BYTES AND TYPE, not just pathnames. Version 1 listed
	names, which authorized the deletion of a recorded pathname holding a FIFO
	or somebody's own text -- neither is an extra or a missing name, so nothing
	could see it. The refusal to record digests was wrong for the stated
	reason: the answer to "an unverified fact is misleading" is to verify it.
	"""
	facts = _facts(staging)
	record = {"format": OWNERSHIP_FORMAT,
	          "format_version": OWNERSHIP_FORMAT_VERSION,
	          "entries": facts}
	with open(os.path.join(staging, OWNERSHIP), "w", encoding="utf-8") as writer:
		json.dump(record, writer, indent=2, sort_keys=True)
		writer.write("\n")


def _unique(pairs):
	"""JSON object hook that refuses duplicate keys.

	`json.loads` keeps the last of a repeated key, so a record could name one
	path twice with different digests and validate against whichever won.
	"""
	seen = {}
	for key, value in pairs:
		if key in seen:
			raise ValueError(f"duplicate key {key!r}")
		seen[key] = value
	return seen


def validate(root: str) -> None:
	"""May this build retire and delete `root`? Anything short of yes refuses.

	SHARED, deliberately: the build asks this before retiring a candidate and
	`tests/candidate.py` asks it before the suite runs, so the preflight and
	the destructive boundary cannot drift into two different opinions about
	what a candidate is.

	Reads the record WITHOUT following links and requires it to be a regular
	file, so a link pointing at a valid record somewhere else cannot vouch for
	a directory. Then recomputes every recorded digest.
	"""
	if not os.listdir(root):
		# AN EMPTY DIRECTORY IS NOT SOMEBODY'S WORK. `mkdir build` before the
		# first build is an ordinary thing to do, and replacing an empty
		# directory removes no bytes at all -- which is the only thing this
		# check exists to protect. Approved 2026-08-13.
		return
	path = os.path.join(root, OWNERSHIP)
	try:
		descriptor = _open_regular(path)
	except BuildError:
		raise
	except OSError:
		raise BuildError(
			f"{root} exists but carries no readable {OWNERSHIP}, so it is not a "
			f"candidate this build produced. Refusing to retire it: remove or "
			f"move it deliberately if the path is meant to hold one.") from None
	try:
		with os.fdopen(descriptor, "r", encoding="utf-8") as reader:
			raw = reader.read()
	except UnicodeDecodeError:
		raise BuildError(f"{path} is not readable text; refusing") from None
	try:
		record = json.loads(raw, object_pairs_hook=_unique)
	except ValueError as broken:
		raise BuildError(f"{path} is not a usable record ({broken}); refusing") \
			from None
	if not isinstance(record, dict):
		raise BuildError(f"{path} is not a JSON object; refusing")
	if record.get("format") != OWNERSHIP_FORMAT:
		raise BuildError(
			f"{path} says format {record.get('format')!r}, not "
			f"{OWNERSHIP_FORMAT!r}; refusing")
	if record.get("format_version") != OWNERSHIP_FORMAT_VERSION:
		raise BuildError(
			f"{path} is format version {record.get('format_version')!r}; this "
			f"build writes {OWNERSHIP_FORMAT_VERSION}. It cannot verify a shape "
			f"it does not know, so it will not delete the tree either: remove "
			f"{root} yourself and build again.")
	entries = record.get("entries")
	if not isinstance(entries, dict) or not entries:
		raise BuildError(f"{path} does not describe its entries; refusing")
	recorded = {}
	for entry, facts in entries.items():
		if (not isinstance(entry, str) or os.path.isabs(entry)
				or entry.startswith("../") or "/../" in entry
				or entry in ("", ".", "..") or entry.endswith("/..")
				or entry != os.path.normpath(entry) or entry == OWNERSHIP):
			raise BuildError(f"{path} names an entry it may not name: {entry!r}")
		if not isinstance(facts, dict):
			raise BuildError(f"{path} does not describe {entry}; refusing")
		digest = facts.get("sha256")
		mode = facts.get("mode")
		if (not isinstance(digest, str) or len(digest) != 64
				or any(character not in "0123456789abcdef" for character in digest)):
			raise BuildError(f"{path} records no usable digest for {entry}")
		if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
			raise BuildError(f"{path} records no usable mode for {entry}")
		recorded[entry] = {"sha256": digest, "mode": mode}

	present = _facts(root)
	present.pop(OWNERSHIP, None)
	extra = sorted(set(present) - set(recorded))
	absent = sorted(set(recorded) - set(present))
	if extra or absent:
		raise BuildError(
			f"{root} does not match its own {OWNERSHIP}"
			+ (f"; it holds {', '.join(extra)}, which no build put there" if extra
			   else "")
			+ (f"; {', '.join(absent)} is recorded but missing" if absent else "")
			+ ". Refusing to retire it.")
	for entry in sorted(recorded):
		if present[entry]["sha256"] != recorded[entry]["sha256"]:
			raise BuildError(
				f"{os.path.join(root, entry)} is not the file this record "
				f"describes: its bytes have changed. Refusing to retire it.")
		if present[entry]["mode"] != recorded[entry]["mode"]:
			raise BuildError(
				f"{os.path.join(root, entry)} is mode "
				f"{present[entry]['mode']:o}, recorded as "
				f"{recorded[entry]['mode']:o}. Refusing to retire it.")


def _publish_candidate(staging: str, root: str) -> list[str]:
	"""Make the prepared tree THE candidate, as one directory-level move.

	SUPERSEDED: this used to replace each payload leaf inside the visible
	`build/` one at a time. Four `os.replace` calls were described as "not one
	transaction", which was true and was also not good enough -- an injected
	failure at the fourth left a candidate holding bytes from two builds, and
	`deploy` reads that path. A mixture is the one state nothing downstream can
	detect, because every individual file is intact.

	So the complete candidate is prepared OUTSIDE `build/` and moved in:

	    rename build -> .build-retiring-<unique>/candidate   (if it exists)
	    rename staging -> build
	    remove the retired tree

	`build/` is briefly ABSENT between those renames, and that is the point:
	absence fails closed -- deploy says "run the build first" -- while a
	mixture does not. Replacing the whole tree also retires stale files from an
	earlier candidate, which a growing list of leaves never could.
	"""
	root = os.path.abspath(root)
	parent = os.path.dirname(root)
	holder = None
	if os.path.lexists(root):
		# RESOLVED AND CHECKED BEFORE ANYTHING MOVES. A symlink or a
		# non-directory here is not a candidate this tool produced, and
		# retiring it would be disposing of somebody else's object -- through
		# a link, of a directory nobody named. `lexists` and `islink` are
		# deliberate: neither follows the link.
		if os.path.islink(root) or not os.path.isdir(root):
			raise BuildError(
				f"{root} exists and is not a directory; refusing to retire an "
				f"object this build did not create")
		# AND IT MUST BE ONE OF OURS. `isdir` alone let an ordinary directory
		# -- somebody's notes, an unrelated tree -- be moved aside and then
		# recursively removed, while this module claimed the old candidate had
		# been resolved and checked.
		validate(root)
		# The old candidate is moved INTO a directory this call just created,
		# rather than onto a name it computed and then unlinked. There is no
		# window in which the retirement name exists unclaimed.
		holder = tempfile.mkdtemp(prefix=f".{os.path.basename(root)}-retiring-",
		                          dir=parent)
		try:
			os.rename(root, os.path.join(holder, "candidate"))
		except BaseException:
			os.rmdir(holder)             # nothing moved; leave no marker behind
			raise
		# VALIDATED AGAIN, ON THE MOVED TREE. The first check answered about a
		# public pathname anybody can write to; between that answer and the
		# `rmtree` below there was a window in which a file could be added,
		# replaced or swapped and then swept into the recursive delete. After
		# the move the tree is only reachable through a name this call created,
		# so this second answer is the one that authorizes deletion -- and if
		# it refuses, the tree goes back where it was, untouched.
		retired = os.path.join(holder, "candidate")
		try:
			validate(retired)
		except BaseException:
			os.rename(retired, root)
			os.rmdir(holder)
			raise
	try:
		os.rename(staging, root)
	except BaseException:
		if holder is not None:                       # put the old one back
			os.rename(os.path.join(holder, "candidate"), root)
			os.rmdir(holder)
		raise
	if holder is not None:
		shutil.rmtree(holder, ignore_errors=True)
	_fsync_dir(parent)
	return sorted(
		os.path.relpath(os.path.join(base, name), root)
		for base, _directories, files in os.walk(root) for name in files)


def _modes(staging: str) -> None:
	"""Fix the permissions the candidate is published with.

	`mkdtemp` makes a 0700 directory, and renaming it into place would publish
	a candidate only its builder could enter. The per-file modes are the ones
	installation used to set explicitly, kept explicit so a build is not
	reading the umask of whoever ran it."""
	os.chmod(staging, 0o755)
	for base, directories, files in os.walk(staging):
		for name in directories:
			os.chmod(os.path.join(base, name), 0o755)
		for name in files:
			path = os.path.join(base, name)
			executable = os.path.relpath(path, staging).split(os.sep)[0] == "bin"
			os.chmod(path, 0o755 if executable else 0o644)


def _fsync_dir(path: str) -> None:
	fd = os.open(path, os.O_RDONLY)
	try:
		os.fsync(fd)
	finally:
		os.close(fd)


def _certifiable(staging: str) -> None:
	"""Would the deployer accept this candidate? Asked here, while a human can
	still fix it, instead of at publication when the set turns out never to
	have been deployable."""
	import deploy                          # sibling tool; HERE is on sys.path

	try:
		deploy.certified(staging)
	except deploy.DeployError as refusal:
		raise BuildError(f"the candidate does not certify: {refusal}") from None


def build(root: str | None = None) -> dict:
	"""Prepare the complete candidate elsewhere, then publish it AS `root`.

	`root` defaults to `build/` and a caller has to be explicit to put a
	candidate anywhere else. Nothing here writes to the checkout, and nothing
	incomplete is ever visible at `root`: the staging tree lives beside it, and
	the only thing done to `root` is a rename.

	The default is resolved HERE rather than bound in the signature: a default
	argument is evaluated once at definition, so `CANDIDATE` could not be
	redirected -- not by a test, and not by anything else that needs the
	default to follow the constant."""
	if root is None:
		root = CANDIDATE
	if os.path.abspath(root) == os.path.abspath(ROOT):
		raise BuildError(
			"refusing to build into the checkout: a successful build would "
			"replace the executables live consumers are running. Build into "
			f"{CANDIDATE} (the default) and publish from there.")
	parent = os.path.dirname(os.path.abspath(root))
	os.makedirs(parent, exist_ok=True)
	# OUTSIDE the candidate pathname, so nothing incomplete is ever visible at
	# the path deploy and the gates read.
	staging = tempfile.mkdtemp(prefix=f".{os.path.basename(root)}-staging-",
	                           dir=parent)
	try:
		manifests = prepare(staging)
		# CERTIFIED BEFORE IT IS PUBLISHED. The deployer would refuse an
		# incoherent set anyway; refusing here means the candidate a human
		# looks at is one that could actually be deployed, and the refusal
		# names the build that produced it.
		_certifiable(staging)
		# Modes first, then the record: the record states the mode of every
		# leaf, so it has to be written after the modes it describes are final.
		_modes(staging)
		# Stamped LAST, so the record describes the finished candidate and a
		# tree that never got one can never be mistaken for a candidate.
		_stamp(staging)
		written = _publish_candidate(staging, root)
	except BaseException:
		shutil.rmtree(staging, ignore_errors=True)
		raise
	return {
		"installed": written,
		"products": {manifest["tool"]: manifest["product_version"]
		             for manifest in manifests.values()},
		"core": next(iter(manifests.values()))["embeds_core"],
	}


if __name__ == "__main__":
	out = sys.argv[1] if len(sys.argv) > 1 else CANDIDATE
	try:
		print(json.dumps(build(out), indent=2, sort_keys=True))
	except BuildError as refusal:
		print(f"build: {refusal}", file=sys.stderr)
		sys.exit(1)
