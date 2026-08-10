"""Participant-local draft storage: where it writes, and what it refuses.

`Esc` used to discard a whole composition. These pin the storage half of the
fix -- the ruled location, the atomicity, the permissions, and the refusals
that keep "your drafts are saved" from being a promise the console cannot
keep.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from baton_tui import drafts
from baton_tui.drafts import DraftError

PARTICIPANT = "acme.implementer"
def _draft(**overrides):
	"""A complete version-1 draft. Every field, because the shape is validated
	on the way in as well as on the way out -- a half-populated draft written
	by a test would have proved the validator was not running."""
	draft = {"id": "compose:new:1", "kind": "compose",
	         "subject": "Half a thought", "body": "unfinished",
	         "to": "acme.reviewer", "attach_path": "",
	         "answering": None, "is_reply": False}
	draft.update(overrides)
	return draft


ONE = [_draft()]


def test_the_ruled_location_and_nothing_else(tmp_path):
	"""`<projection_dir>/.baton-tui/<participant>.json`, ruled.

	Asserted as the WHOLE path rather than as "somewhere under the projection
	directory", because the ruling names each component for a separate reason:
	the hidden subdirectory keeps drafts out of the namespace `doctor`
	inventories, and the participant filename is what makes two participants
	sharing a projection directory not share drafts."""
	written = drafts.save(str(tmp_path), PARTICIPANT, ONE)
	assert written == str(tmp_path / ".baton-tui" / "acme.implementer.json")
	assert drafts.load(str(tmp_path), PARTICIPANT) == ONE


def test_two_participants_do_not_share_drafts(tmp_path):
	drafts.save(str(tmp_path), "acme.implementer", ONE)
	drafts.save(str(tmp_path), "acme.reviewer", [])
	assert drafts.load(str(tmp_path), "acme.implementer") == ONE
	assert drafts.load(str(tmp_path), "acme.reviewer") == []


def test_no_drafts_yet_is_not_an_error(tmp_path):
	"""The ordinary state of someone who has never left a draft. Reporting it
	as a failure would put an error on the status bar at every start."""
	assert drafts.load(str(tmp_path), PARTICIPANT) == []


def test_the_directory_is_private_and_so_is_the_file(tmp_path):
	"""A draft is unsent private writing. It is the one thing here that is
	nobody else's business, and on a shared host the default umask is not a
	policy anyone chose."""
	path = drafts.save(str(tmp_path), PARTICIPANT, ONE)
	directory = tmp_path / ".baton-tui"
	assert stat.S_IMODE(os.stat(directory).st_mode) == 0o700
	assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_no_projection_directory_is_refused_with_the_remedy(tmp_path):
	"""NOT a silent fallback to `$HOME` or XDG. A draft written somewhere the
	human did not choose is a private document filed where they will not look
	for it, and "your drafts are saved" has to be true."""
	with pytest.raises(DraftError) as caught:
		drafts.save("", PARTICIPANT, ONE)
	message = str(caught.value)
	assert "projection_dir" in message, message
	assert "baton.json" in message, message


def test_a_relative_projection_directory_is_refused(tmp_path):
	"""It would resolve against whatever directory the console was started
	from, so the same participant would get different drafts depending on
	where they launched it -- a difference nobody would think to look for."""
	with pytest.raises(DraftError) as caught:
		drafts.save("relative/dir", PARTICIPANT, ONE)
	assert "absolute" in str(caught.value)


@pytest.mark.parametrize("address", [
	"../escape", "acme.implementer/../../x", "/absolute", "no-domain",
	".leading", "acme.", "ACME.Implementer", "", "acme.impl/ementer",
])
def test_a_filename_is_never_derived_from_an_unvalidated_address(address):
	"""The address grammar has no separator, so a conforming address is
	already a safe single component -- this checks instead of assuming.

	REFUSED rather than sanitized, the same rule reference paths and part
	field names follow. A filename built from an identity is exactly where a
	silent cleanup turns into writing over someone else's drafts."""
	with pytest.raises(DraftError):
		drafts.filename(address)


def test_a_valid_address_is_the_file_component_unchanged(tmp_path):
	assert drafts.filename("acme.implementer") == "acme.implementer.json"
	assert drafts.filename("org.team.lead") == "org.team.lead.json"


def test_an_unreadable_draft_file_is_reported_and_left_alone(tmp_path):
	"""The human's unsent writing is in there. Overwriting it so the console
	starts cleanly is the one repair that must never happen by itself."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	path = tmp_path / ".baton-tui" / "acme.implementer.json"
	path.write_text("{ not json")
	path.chmod(0o600)
	with pytest.raises(DraftError) as caught:
		drafts.load(str(tmp_path), PARTICIPANT)
	assert str(path) in str(caught.value)
	assert path.read_text() == "{ not json", "the file was modified"


def test_an_unreadable_file_diagnostic_does_not_echo_its_contents(tmp_path):
	"""A draft body is private, and a parse error is not a reason to put it on
	a terminal that may be shared, logged or screen-shared."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	path = tmp_path / ".baton-tui" / "acme.implementer.json"
	path.write_text("SECRET DRAFT TEXT { not json")
	path.chmod(0o600)
	with pytest.raises(DraftError) as caught:
		drafts.load(str(tmp_path), PARTICIPANT)
	assert "SECRET DRAFT TEXT" not in str(caught.value)


def test_a_future_version_is_refused_rather_than_guessed_at(tmp_path):
	"""Reading a newer file with older rules is how a draft comes back subtly
	different from what was written."""
	directory = tmp_path / ".baton-tui"
	directory.mkdir(mode=0o700)
	stored = directory / "acme.implementer.json"
	stored.write_text(json.dumps({"version": drafts.VERSION + 1, "drafts": []}))
	stored.chmod(0o600)
	with pytest.raises(DraftError) as caught:
		drafts.load(str(tmp_path), PARTICIPANT)
	assert "version" in str(caught.value)


def test_a_failed_write_leaves_the_previous_drafts_intact(tmp_path, monkeypatch):
	"""Atomicity, asserted by breaking the write rather than by reading the
	code. Whole-file replacement means a crash mid-write could otherwise
	truncate every draft the participant had."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	path = tmp_path / ".baton-tui" / "acme.implementer.json"
	before = path.read_bytes()

	def explode(*_args, **_kwargs):
		raise OSError(28, "No space left on device")

	monkeypatch.setattr(os, "replace", explode)
	with pytest.raises(DraftError):
		drafts.save(str(tmp_path), PARTICIPANT,
		            [_draft(subject="newer")])
	assert path.read_bytes() == before, "the previous drafts were damaged"


def test_a_failed_write_leaves_no_temporary_file_behind(tmp_path, monkeypatch):
	"""A half-written file found later is worse than none: it looks like a
	draft and is not one."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)

	def explode(*_args, **_kwargs):
		raise OSError(28, "No space left on device")

	monkeypatch.setattr(os, "replace", explode)
	with pytest.raises(DraftError):
		drafts.save(str(tmp_path), PARTICIPANT, ONE)
	leftovers = [p.name for p in (tmp_path / ".baton-tui").iterdir()
	             if p.name.startswith(".tmp-")]
	assert leftovers == [], leftovers


def test_saving_replaces_rather_than_appends(tmp_path):
	"""The caller holds the whole list. A partial update is how two drafts end
	up disagreeing about which one is current."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	drafts.save(str(tmp_path), PARTICIPANT, [])
	assert drafts.load(str(tmp_path), PARTICIPANT) == []


def test_the_round_trip_preserves_non_ascii_and_order(tmp_path):
	"""Subjects and bodies are human text. A draft that comes back
	transliterated is a different draft."""
	many = [_draft(id=f"compose:new:{i}", subject=f"n°{i} — café",
	               body="✓ done\n") for i in range(3)]
	drafts.save(str(tmp_path), PARTICIPANT, many)
	assert drafts.load(str(tmp_path), PARTICIPANT) == many


def test_storage_reaches_no_authority(tmp_path, monkeypatch):
	"""The property that keeps a draft a local convenience rather than a
	second, weaker mailbox: retaining one publishes nothing, claims nothing,
	completes nothing, and records no audit.

	Asserted by making the whole core explode if this module so much as
	imports it."""
	import sys
	sentinel = object()

	class Poisoned:
		def __getattr__(self, name):
			pytest.fail(f"draft storage reached the authority: baton_core.{name}")

	monkeypatch.setitem(sys.modules, "baton_core", Poisoned())
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	assert drafts.load(str(tmp_path), PARTICIPANT) == ONE
	assert sentinel is sentinel


# -- the ruled filesystem boundary -----------------------------------------

def test_a_missing_projection_directory_is_refused_not_created(tmp_path):
	"""Ruled: an EXISTING absolute directory. Creating it would put private
	writing somewhere the deployment never configured, which is a
	home-directory fallback with extra steps."""
	missing = tmp_path / "not-there"
	with pytest.raises(DraftError) as caught:
		drafts.save(str(missing), PARTICIPANT, ONE)
	assert "does not exist" in str(caught.value)
	assert not missing.exists(), "the projection directory was created"


def test_a_symlinked_namespace_is_refused_and_the_target_untouched(tmp_path):
	"""Following it would write private drafts outside the configured
	directory while every message the console prints still names the
	configured path. The human would have no way to know where their writing
	went."""
	elsewhere = tmp_path / "elsewhere"
	elsewhere.mkdir()
	home = tmp_path / "proj"
	home.mkdir()
	(home / ".baton-tui").symlink_to(elsewhere)
	with pytest.raises(DraftError) as caught:
		drafts.save(str(home), PARTICIPANT, ONE)
	assert "symlink" in str(caught.value)
	assert list(elsewhere.iterdir()) == [], "wrote through the symlink"


def test_a_symlinked_participant_file_is_refused_on_save_and_load(tmp_path):
	elsewhere = tmp_path / "outside.json"
	elsewhere.write_text("untouched")
	home = tmp_path / "proj"
	home.mkdir()
	namespace = home / ".baton-tui"
	namespace.mkdir(mode=0o700)
	(namespace / "acme.implementer.json").symlink_to(elsewhere)
	for call in (lambda: drafts.save(str(home), PARTICIPANT, ONE),
	             lambda: drafts.load(str(home), PARTICIPANT)):
		with pytest.raises(DraftError) as caught:
			call()
		assert "symlink" in str(caught.value)
	assert elsewhere.read_text() == "untouched"


def test_a_non_directory_namespace_is_refused(tmp_path):
	home = tmp_path / "proj"
	home.mkdir()
	(home / ".baton-tui").write_text("a file, not a directory")
	with pytest.raises(DraftError) as caught:
		drafts.save(str(home), PARTICIPANT, ONE)
	assert "not a directory" in str(caught.value)


def test_a_public_pre_existing_namespace_is_refused_not_tightened(tmp_path):
	"""NOT silently chmodded. Someone chose those permissions or something
	else created the directory; changing them behind the human's back is its
	own surprise, and writing private drafts into a world-readable directory
	is the harm."""
	home = tmp_path / "proj"
	home.mkdir()
	(home / ".baton-tui").mkdir(mode=0o755)
	with pytest.raises(DraftError) as caught:
		drafts.save(str(home), PARTICIPANT, ONE)
	message = str(caught.value)
	assert "not private" in message and "0755" in message


def test_the_directory_entry_is_fsynced_after_the_replace(tmp_path, monkeypatch):
	"""`os.replace` is atomic for readers, but the directory ENTRY is not
	durable until the directory is synced -- so a power loss can leave the
	name pointing at nothing while both files' contents are safely on disk.

	Asserted by recording what was fsynced, because the durability itself
	cannot be observed from inside the process."""
	synced = []
	real_fsync = os.fsync

	def record(fd):
		try:
			synced.append(os.fstat(fd).st_mode)
		finally:
			real_fsync(fd)

	monkeypatch.setattr(os, "fsync", record)
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	assert any(stat.S_ISDIR(mode) for mode in synced), \
		"the containing directory was never fsynced"
	assert any(stat.S_ISREG(mode) for mode in synced), \
		"the temporary file was never fsynced"


# -- strict shape, fail closed ---------------------------------------------

@pytest.mark.parametrize("drafts_value,fragment", [
	([1], "not an object"),
	([{"id": "a"}], "not text"),
	([_draft(id="")], "empty id"),
	([_draft(kind="nonsense")], "unknown kind"),
	([_draft(answering=5)], "not a message id"),
	([_draft(is_reply="yes")], "not a boolean"),
	([_draft(), _draft()], "duplicate id"),
])
def test_a_syntactically_valid_but_corrupt_file_fails_closed(
		tmp_path, drafts_value, fragment):
	"""Validating only the outer shape meant `{"drafts": [1]}` loaded as
	healthy and took the console down one screen later, at the row builder --
	where it reads as an application bug rather than an intact file that needs
	looking at."""
	directory = tmp_path / ".baton-tui"
	directory.mkdir(mode=0o700)
	path = directory / "acme.implementer.json"
	path.write_text(json.dumps({"version": drafts.VERSION,
	                            "drafts": drafts_value}))
	# A real stored file is 0600, and the mode is checked before the content.
	# Writing it at the default mode would make this assert the wrong refusal.
	path.chmod(0o600)
	before = path.read_text()
	with pytest.raises(DraftError) as caught:
		drafts.load(str(tmp_path), PARTICIPANT)
	assert fragment in str(caught.value)
	assert path.read_text() == before, "the damaged file was not preserved"


def test_a_malformed_draft_is_refused_on_the_way_out_too(tmp_path):
	"""Validating only on load would let this process write the corruption the
	next one refuses to read."""
	with pytest.raises(DraftError):
		drafts.save(str(tmp_path), PARTICIPANT, [{"id": "x"}])


def test_a_public_participant_file_is_refused_on_load_and_save(tmp_path):
	"""RR1. Displaying private drafts out of a world-readable file would tell
	the human their writing is private when it is not; silently re-chmodding
	it hides that it ever was not. Refusing says both.

	The file and its bytes survive the refusal: the words in there are the
	human's, and a permission problem is not a reason to touch them."""
	drafts.save(str(tmp_path), PARTICIPANT, ONE)
	path = tmp_path / ".baton-tui" / "acme.implementer.json"
	before = path.read_bytes()
	path.chmod(0o644)
	for call in (lambda: drafts.load(str(tmp_path), PARTICIPANT),
	             lambda: drafts.save(str(tmp_path), PARTICIPANT, ONE)):
		with pytest.raises(DraftError) as caught:
			call()
		message = str(caught.value)
		assert "not private" in message and "0644" in message, message
	assert path.read_bytes() == before, "the refusal modified the file"
	assert stat.S_IMODE(os.stat(path).st_mode) == 0o644, \
		"the refusal changed the permissions it was complaining about"
