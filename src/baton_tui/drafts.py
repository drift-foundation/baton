"""Participant-local draft storage.

`Esc` used to discard a whole composition. It is a navigation key -- the one
people press to back out of anything -- so it was also, silently, the most
destructive key on the console. Drafts are now retained and only `D` with a
confirmation discards one.

WHERE. Ruled: `<projection_dir>/.baton-tui/<participant>.json`, a hidden
namespace inside the participant's own explicitly configured projection
directory. Not beside the authority database, where it would be an
unrecognized artifact in a directory `doctor` inventories; not under `$HOME`
or XDG, which is a sandbox surprise waiting to happen; not in a repository
working tree.

THIS IS NOT PROTOCOL STATE. Nothing here reaches the authority. Retaining,
listing, reopening or discarding a draft publishes nothing, claims nothing,
completes nothing and records no audit -- which is the property that lets a
draft be a purely local convenience rather than a second, weaker mailbox.

NO IMPLICIT DIRECTORY. Draft persistence requires a configured, existing,
absolute `projection_dir`. When there is not one, this module says so and the
console tells the human how to configure it. It does NOT invent a location,
because a draft written somewhere the human did not choose is a private
document filed where they will not look for it -- and "your drafts are saved"
is a promise that must be true.

ATOMIC, AND PRIVATE. The file is written to a temporary name in the same
directory and renamed over the target, so a crash mid-write leaves the
previous drafts rather than a truncated file. The directory is `0700` and the
file `0600`: a draft is unsent private writing, and it is the one thing here
that is nobody else's business. Bodies are never logged.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile

# Spelled out rather than compiled. The console is held to a small stdlib
# allowlist -- `test_packaging_isolation` enumerates it -- and `re` is not on
# it, which is a boundary worth keeping for two dozen characters of grammar.
_LABEL_START = "abcdefghijklmnopqrstuvwxyz"
_LABEL_REST = _LABEL_START + "0123456789_"


def _is_participant(address) -> bool:
	"""The authority's participant grammar: dot-separated lowercase labels,
	at least two of them.

	Applied here because this builds a FILENAME. The address is already
	validated upstream, but a filename derived from an identity is exactly
	where a silent sanitize turns into writing over someone else's drafts, so
	it is checked again and REFUSED rather than repaired -- the same rule
	reference paths and part field names follow.
	"""
	if not isinstance(address, str):
		return False
	labels = address.split(".")
	if len(labels) < 2:
		return False
	return all(label and label[0] in _LABEL_START
	           and all(character in _LABEL_REST for character in label)
	           for label in labels)


DIRECTORY = ".baton-tui"
DIR_MODE = 0o700
FILE_MODE = 0o600
# The version this console WRITES. It advanced to 2 when notice drafts gained
# an audience, and the bump is the whole point rather than bookkeeping: a
# version-1 file carrying an extra field is still a version-1 file to every
# reader that already exists, and the frozen 1.0 console reads exactly those --
# ignoring the audience it does not know about and publishing the notice to
# everyone. A new version is what makes an older console REFUSE the file
# instead of misreading it.
VERSION = 3

# What this console can READ.
#
# 1 predates scoped notices: its notice drafts were global by construction and
#   migrate to an explicit `*`.
# 2 predates the full-body intent marker: `body_requested` is derived on read
#   from whether a body is present, which is the best available answer and the
#   one the console used before the marker existed.
#
# The bump to 3 exists for the same reason the bump to 2 did, and I needed
# telling twice: adding an OPTIONAL field leaves every existing reader
# accepting the file and silently dropping the protection it carries. A version
# an older reader refuses is the only way to stop that.
READABLE = (1, 2, 3)


class DraftError(Exception):
	"""A draft could not be stored or read.

	Deliberately NOT `BatonError`: nothing here is a protocol operation, and
	borrowing the authority's error type would make a local filesystem problem
	look like the mailbox refusing something.
	"""


def filename(participant: str) -> str:
	"""The file component for one participant, validated rather than cleaned.

	The address grammar contains no `/`, no `..` and no leading dot, so a
	conforming address is already a safe single component. This checks instead
	of assuming, because the cost of being wrong is writing outside the
	directory the ruling named.
	"""
	if not _is_participant(participant):
		raise DraftError(f"not a participant address: {participant!r}")
	return f"{participant}.json"


def directory(projection_dir: str) -> str:
	"""The hidden namespace inside a participant's projection directory.

	The projection directory must EXIST and be a real directory. Creating it
	would put private writing somewhere the deployment never configured, which
	is the same harm as a home-directory fallback with extra steps: ruled out.

	Refuses a relative path outright. A relative projection directory would
	resolve against whatever the console's working directory happened to be,
	so the same participant would get different drafts depending on where they
	started the console -- a difference nobody would think to look for.
	"""
	if not projection_dir:
		raise DraftError(
			"no projection directory is configured for this participant; "
			"set projection_dir in baton.json to keep drafts")
	if not os.path.isabs(projection_dir):
		raise DraftError(
			"projection_dir must be an absolute path to keep drafts")
	if not os.path.isdir(projection_dir):
		raise DraftError(
			f"projection_dir does not exist: {projection_dir}; create it or "
			f"correct baton.json to keep drafts")
	return os.path.join(projection_dir, DIRECTORY)


def _checked_namespace(projection_dir: str) -> str:
	"""The hidden directory, refusing anything that is not one.

	A SYMLINK here is refused rather than followed. Following it would write
	private drafts wherever it points -- outside the configured projection
	directory, possibly outside the participant's own space -- while every
	message the console prints still names the configured path. The human
	would have no way to know where their writing actually went.

	`lstat`, not `stat`: the question is what the NAME is, not what it leads
	to. Refusing to create it when the projection directory is missing is
	handled a level up.
	"""
	target = directory(projection_dir)
	try:
		info = os.lstat(target)
	except FileNotFoundError:
		return target
	except OSError as error:
		raise DraftError(f"cannot use the draft directory: {error.strerror}") from None
	if stat.S_ISLNK(info.st_mode):
		raise DraftError(
			f"the draft directory is a symlink and will not be followed: {target}")
	if not stat.S_ISDIR(info.st_mode):
		raise DraftError(f"the draft directory is not a directory: {target}")
	if stat.S_IMODE(info.st_mode) != DIR_MODE:
		# NOT silently tightened. Someone chose those permissions, or
		# something else created the directory; changing them behind the
		# human's back is its own surprise, and writing private drafts into a
		# world-readable directory is the harm this refuses.
		raise DraftError(
			f"the draft directory is not private (mode "
			f"{stat.S_IMODE(info.st_mode):04o}, expected {DIR_MODE:04o}): {target}")
	return target


def _checked_target(target_dir: str, participant: str) -> str:
	"""The participant file, refusing a symlink or a non-regular file."""
	path = os.path.join(target_dir, filename(participant))
	try:
		info = os.lstat(path)
	except FileNotFoundError:
		return path
	except OSError as error:
		raise DraftError(f"cannot use the draft file: {error.strerror}") from None
	if stat.S_ISLNK(info.st_mode):
		raise DraftError(
			f"the draft file is a symlink and will not be followed: {path}")
	if not stat.S_ISREG(info.st_mode):
		raise DraftError(f"the draft file is not a regular file: {path}")
	if stat.S_IMODE(info.st_mode) != FILE_MODE:
		# NOT silently re-chmodded, and NOT read anyway. Displaying private
		# drafts out of a world-readable file would tell the human their
		# writing is private when it is not, and quietly tightening the mode
		# hides that it ever was not. Refusing says both.
		raise DraftError(
			f"the draft file is not private (mode "
			f"{stat.S_IMODE(info.st_mode):04o}, expected {FILE_MODE:04o}): {path}")
	return path


def load(projection_dir: str, participant: str) -> list[dict]:
	"""Every retained draft for this participant, oldest first.

	A MISSING file is not an error -- it is the ordinary state of a
	participant who has never left a draft. A file that exists and cannot be
	parsed IS an error, and is reported rather than silently replaced: the
	human's unsent writing is in there, and overwriting it to make the console
	start cleanly is the one repair that must never happen automatically.
	"""
	path = _checked_target(_checked_namespace(projection_dir), participant)
	try:
		with open(path, "rb") as handle:
			raw = handle.read()
	except FileNotFoundError:
		return []
	except OSError as error:
		raise DraftError(f"cannot read drafts: {error.strerror}") from None
	try:
		document = json.loads(raw.decode("utf-8"))
	except (ValueError, UnicodeDecodeError):
		# The path is named, the CONTENT is not: a draft body is private and
		# a parse error is not a reason to put it on a terminal.
		raise DraftError(
			f"the draft file is unreadable and was left untouched: {path}") from None
	version = document.get("version") if isinstance(document, dict) else None
	if version not in READABLE:
		raise DraftError(
			f"the draft file is a version this console does not read: {path}")
	drafts = document.get("drafts")
	if not isinstance(drafts, list):
		raise DraftError(f"the draft file has no draft list: {path}")
	if version == 1:
		drafts = [_migrated_from_v1(draft) for draft in drafts]
	if version in (1, 2):
		drafts = [_migrated_to_v3(draft) for draft in drafts]
	try:
		_validate(drafts, where=path)
	except DraftError:
		# FAIL CLOSED, and leave the file alone. The alternative -- returning
		# what parsed and skipping the rest -- turns corruption into a console
		# crash later, at the row builder, where it reads as an application
		# bug rather than an intact file that needs looking at.
		raise
	return drafts


# Every field a draft carries, and what it must be. Text fields are
# checked as `str` rather than coerced: a draft body that came back as the
# string "None" because something was None is a different draft.
_TEXT_FIELDS = ("id", "kind", "subject", "body", "to", "attach_path")
_KINDS = ("compose", "notice", "reply")
# The notice AUDIENCE. Optional on read, because drafts written before scoped
# notices existed do not carry it -- those are global by construction and are
# restored as an explicit `*` rather than rejected. Required to be text when
# present: a retained team notice that came back without its audience would be
# published to everyone, which is the one outcome this whole feature exists to
# prevent.
_SCOPE_FIELD = "notice_scope"

# The audience spelling for "everyone", duplicated from the state module on
# purpose: this file is the storage format and must not import the screen
# model to read a file. One constant, two names, and a test asserts they agree.
GLOBAL_SCOPE = "*"


def _migrated_from_v1(draft):
	"""A version-1 draft's AUDIENCE, read as the current format means it.

	Version 1 predates scoped notices, so a notice written then was global by
	construction and becomes an explicit `*`. An EXPERIMENTAL v1 file that
	already carries an audience -- this console wrote such files briefly --
	keeps it: the value is preserved and validated like any other, never
	downgraded to global, because downgrading is exactly the failure the
	version bump exists to stop.

	Migration happens on READ and is not written back here. The file is
	rewritten as the CURRENT version the next time drafts are saved, which is
	the only moment this console is entitled to touch the human's unsent
	writing.
	"""
	if not isinstance(draft, dict) or draft.get("kind") != "notice":
		return draft
	if _SCOPE_FIELD in draft:
		# PRESENT, whatever it says. Testing truthiness here migrated an EMPTY
		# audience to `*` -- silently turning a damaged team notice into a
		# mailbox-wide broadcast, which is the downgrade this whole version
		# bump exists to prevent. Absence means "written before audiences
		# existed"; an empty string means "this field lost its value", and
		# only the first has a safe answer.
		return draft
	migrated = dict(draft)
	migrated["notice_scope"] = GLOBAL_SCOPE
	return migrated


def _migrated_to_v3(draft):
	"""A draft from before the full-body intent marker existed.

	Derive it from whether a body is present -- which is exactly what the
	console did before the marker, so nothing changes meaning -- and keep a
	value that is already there. A file written by an experimental build with
	the field is preserved, never recomputed.
	"""
	if not isinstance(draft, dict):
		return draft
	if isinstance(draft.get("body_requested"), bool):
		return draft
	migrated = dict(draft)
	migrated["body_requested"] = bool(draft.get("body"))
	return migrated


def _validate(drafts, *, where: str) -> None:
	"""Refuse anything that is not a complete, unique CURRENT-version draft
	list.

	The row builder dereferences these as mappings. Validating only the outer
	shape meant a file containing `{"drafts": [1]}` loaded as healthy and took
	the console down one screen later.

	Duplicate IDs are refused too: the id is what update, reopen and discard
	all select on, so two rows sharing one would make every one of those
	operations ambiguous -- and discard ambiguous in the destructive
	direction.
	"""
	seen = set()
	for index, draft in enumerate(drafts):
		place = f"{where}: draft {index}"
		if not isinstance(draft, dict):
			raise DraftError(f"{place} is not an object")
		for field in _TEXT_FIELDS:
			value = draft.get(field)
			if not isinstance(value, str):
				raise DraftError(f"{place}: {field!r} is not text")
		if not draft["id"]:
			raise DraftError(f"{place}: empty id")
		if draft["kind"] not in _KINDS:
			raise DraftError(f"{place}: unknown kind {draft['kind']!r}")
		answering = draft.get("answering")
		if answering is not None and not isinstance(answering, str):
			raise DraftError(f"{place}: 'answering' is not a message id")
		if not isinstance(draft.get("is_reply"), bool):
			raise DraftError(f"{place}: 'is_reply' is not a boolean")
		requested = draft.get("body_requested")
		if not isinstance(requested, bool):
			# REQUIRED in this format, for every kind. Absent, its meaning
			# would have to be guessed, and the permissive guess is the one
			# that sends a subject line in place of a body someone deleted.
			raise DraftError(f"{place}: 'body_requested' is missing or not a boolean")
		scope = draft.get(_SCOPE_FIELD)
		if draft["kind"] == "notice" and scope is None:
			# REQUIRED in this format. A notice draft with no audience is one
			# whose reach would be decided at send time by whatever the reader
			# defaults to, and that default is "everyone".
			raise DraftError(f"{place}: notice draft has no {_SCOPE_FIELD!r}")
		if scope is not None and not isinstance(scope, str):
			raise DraftError(f"{place}: {_SCOPE_FIELD!r} is not text")
		if scope is not None and not scope:
			# An EMPTY string is not "global" -- it is a field that was written
			# and lost its value, and guessing which audience it meant is
			# exactly the guess that broadcasts a team message to everyone.
			raise DraftError(f"{place}: {_SCOPE_FIELD!r} is empty")
		if draft["id"] in seen:
			raise DraftError(f"{place}: duplicate id {draft['id']!r}")
		seen.add(draft["id"])


def save(projection_dir: str, participant: str, drafts: list[dict]) -> str:
	"""Write every draft atomically. Returns the path written.

	Whole-file, not append: the caller holds the full list, and a partial
	update is how two drafts end up disagreeing about which one is current.
	"""
	target_dir = _checked_namespace(projection_dir)
	_validate(drafts, where="drafts to save")
	document = json.dumps({"version": VERSION, "drafts": drafts},
	                      ensure_ascii=False, sort_keys=True, indent=1)
	path = _checked_target(target_dir, participant)
	try:
		# The hidden namespace is created; the PROJECTION directory is not.
		# `_checked_namespace` has already refused a missing projection
		# directory, a symlink here, and a non-private existing one.
		os.makedirs(target_dir, mode=DIR_MODE, exist_ok=True)
		# `mkstemp` creates 0600 and in the SAME directory, which is what
		# makes the rename atomic -- across filesystems it would not be.
		handle, temporary = tempfile.mkstemp(dir=target_dir, prefix=".tmp-")
		try:
			with os.fdopen(handle, "w", encoding="utf-8") as stream:
				stream.write(document)
				stream.flush()
				os.fsync(stream.fileno())
			os.chmod(temporary, FILE_MODE)
			os.replace(temporary, path)
			# FSYNC THE DIRECTORY. `os.replace` is atomic with respect to
			# readers, but the DIRECTORY ENTRY is not durable until the
			# directory itself is synced -- so a power loss here can leave the
			# old name pointing at nothing while both files' contents are
			# safely on disk. Ruled, and the one part of the write that
			# inspection rather than a test has to establish.
			handle = os.open(target_dir, os.O_RDONLY)
			try:
				os.fsync(handle)
			finally:
				os.close(handle)
		except BaseException:
			# The previous file is still intact; the half-written one is not
			# left behind to be found later and wondered about.
			try:
				os.unlink(temporary)
			except OSError:
				pass
			raise
	except OSError as error:
		raise DraftError(f"cannot save drafts: {error.strerror}") from None
	return path
