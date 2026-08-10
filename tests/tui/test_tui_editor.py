"""External body editor: resolution, argv safety, temp-file handling.

The text being edited is HOSTILE, the editor command is CONFIGURATION, and the
draft lands in a temporary file. Each of those is a boundary, and each is
tested here rather than assumed.
"""

from __future__ import annotations

import os
import stat

import pytest

from baton_tui.editor import (DEFAULT_EDITOR, MAX_DRAFT_BYTES, edit_text,
                              quote, resolve_editor)


# -- resolution precedence -------------------------------------------------

def test_precedence_is_override_then_baton_then_visual_then_editor():
	env = {"BATON_EDITOR": "baton-ed", "VISUAL": "visual-ed", "EDITOR": "editor-ed"}
	assert resolve_editor("flag-ed", env)[0] == "flag-ed"
	assert resolve_editor(None, env)[0] == "baton-ed"
	assert resolve_editor(None, {k: v for k, v in env.items()
	                             if k != "BATON_EDITOR"})[0] == "visual-ed"
	assert resolve_editor(None, {"EDITOR": "editor-ed"})[0] == "editor-ed"
	assert resolve_editor(None, {})[0] == DEFAULT_EDITOR


@pytest.mark.parametrize("value", ["", "   ", None])
def test_an_empty_setting_falls_through_rather_than_becoming_the_editor(value):
	"""`EDITOR=` set to nothing is not a request to run nothing."""
	assert resolve_editor(None, {"VISUAL": value, "EDITOR": "real-ed"})[0] == "real-ed"


def test_a_configured_editor_keeps_its_arguments():
	assert resolve_editor("code --wait -n", {}) == ["code", "--wait", "-n"]


# -- argv safety: never a shell -------------------------------------------

@pytest.mark.parametrize("hostile", [
	"vim; rm -rf /tmp/pwned",
	"vim && touch /tmp/pwned",
	"vim | tee /tmp/pwned",
	"vim $(touch /tmp/pwned)",
	"vim `touch /tmp/pwned`",
	"vim > /tmp/pwned",
])
def test_shell_metacharacters_become_ordinary_arguments(hostile, tmp_path):
	"""Parsed, never evaluated. A configured editor may have arguments; it may
	not have a pipeline, a redirect, a substitution or a second command.

	The metacharacter survives as INERT TEXT -- `vim;` is simply a program
	name that does not exist, and the launch fails visibly. What must not
	happen is a second command running."""
	seen = {}

	def runner(command):
		seen["command"] = command
		raise FileNotFoundError(command[0])

	argv = resolve_editor(hostile, {})
	result, message = edit_text("draft", argv=argv, runner=runner,
	                            tmpdir=str(tmp_path))
	assert result is None and "not found" in message
	# ONE program was attempted, and the shell operator is just an argument.
	command = seen["command"]
	assert command[0] == argv[0]
	assert not os.path.exists("/tmp/pwned")
	# Nothing was expanded: the substitution text is still literally present.
	if "$(" in hostile or "`" in hostile:
		assert any("touch" in part for part in command)


def test_the_file_is_appended_as_exactly_one_argument(tmp_path):
	seen = {}

	def runner(command):
		seen["command"] = command
		return 0

	edit_text("x", argv=["my ed"] if False else ["myeditor"], runner=runner,
	          tmpdir=str(tmp_path))
	command = seen["command"]
	assert command[0] == "myeditor"
	assert len(command) == 2, "the path was split or extra arguments appeared"
	assert os.path.dirname(command[-1]) == str(tmp_path)


def test_double_dash_is_added_only_for_known_editors(tmp_path):
	"""`--` means end-of-options for vim. Appending it to an arbitrary
	configured command could hand a literal argument to something that does
	not treat it that way."""
	seen = {}

	def runner(command):
		seen.setdefault("commands", []).append(command)
		return 0

	edit_text("x", argv=resolve_editor(None, {}), runner=runner, tmpdir=str(tmp_path))
	edit_text("x", argv=["someeditor"], runner=runner, tmpdir=str(tmp_path))
	vim_command, other_command = seen["commands"]
	assert "--" in vim_command
	assert "--" not in other_command


def test_the_default_invocation_disables_modelines():
	"""A modeline is a line INSIDE the text that configures the editor, and
	this text arrived from another participant."""
	argv = resolve_editor(None, {})
	assert "set nomodeline" in argv


def test_a_user_supplied_vim_invocation_is_left_alone():
	"""Their configuration, their choice. Second-guessing it would be worse
	than honouring it -- and it is an explicit trust boundary either way."""
	assert resolve_editor("vim -u ~/.vimrc.messages", {}) == [
		"vim", "-u", "~/.vimrc.messages"]


# -- the temporary draft ---------------------------------------------------

def test_the_draft_file_is_private_and_regular(tmp_path):
	observed = {}

	def runner(command):
		path = command[-1]
		observed["mode"] = os.lstat(path).st_mode
		return 0

	edit_text("secret", argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert stat.S_ISREG(observed["mode"])
	assert stat.S_IMODE(observed["mode"]) == 0o600


def test_the_draft_file_is_removed_afterwards(tmp_path):
	seen = {}

	def runner(command):
		seen["path"] = command[-1]
		return 0

	edit_text("x", argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert not os.path.exists(seen["path"])
	assert list(tmp_path.iterdir()) == []


def test_the_draft_file_is_removed_even_when_the_editor_fails(tmp_path):
	seen = {}

	def runner(command):
		seen["path"] = command[-1]
		return 3

	assert edit_text("x", argv=["ed"], runner=runner, tmpdir=str(tmp_path))[0] is None
	assert not os.path.exists(seen["path"])


def test_a_symlink_swapped_in_while_editing_is_refused(tmp_path):
	"""The classic temp-file race. Refusing costs one retry; accepting would
	import a file we never wrote."""
	target = tmp_path / "elsewhere"
	target.write_text("attacker content")

	def runner(command):
		path = command[-1]
		os.unlink(path)
		os.symlink(target, path)
		return 0

	result, message = edit_text("x", argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert result is None
	assert "attacker content" not in (result or "")
	# Refused at OPEN time by O_NOFOLLOW, rather than after the fact. The
	# message names whichever gate caught it; what matters is that nothing was
	# imported.
	assert any(marker in message for marker in
	           ("reopened", "regular file", "replaced"))


def test_a_replaced_file_is_refused(tmp_path):
	def runner(command):
		path = command[-1]
		os.unlink(path)
		with open(path, "w") as fh:
			fh.write("different inode")
		return 0

	result, message = edit_text("x", argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert result is None
	assert "replaced" in message


def test_an_oversized_draft_is_refused(tmp_path):
	def runner(command):
		with open(command[-1], "w") as fh:
			fh.write("x" * (MAX_DRAFT_BYTES + 1))
		return 0

	result, message = edit_text("x", argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert result is None
	assert "larger than" in message


# -- editor outcomes -------------------------------------------------------

def test_a_missing_editor_changes_nothing(tmp_path):
	def runner(command):
		raise FileNotFoundError(command[0])

	result, message = edit_text("kept", argv=["nosucheditor"], runner=runner,
	                            tmpdir=str(tmp_path))
	assert result is None
	assert "not found" in message


def test_a_nonzero_exit_changes_nothing(tmp_path):
	result, message = edit_text("kept", argv=["ed"], runner=lambda c: 1,
	                            tmpdir=str(tmp_path))
	assert result is None
	assert "exited 1" in message


def test_a_signal_changes_nothing(tmp_path):
	"""`subprocess.call` reports a signal as a negative status."""
	result, message = edit_text("kept", argv=["ed"], runner=lambda c: -9,
	                            tmpdir=str(tmp_path))
	assert result is None
	assert "signal 9" in message


def test_undecodable_bytes_change_nothing(tmp_path):
	def runner(command):
		with open(command[-1], "wb") as fh:
			fh.write(b"\xff\xfe not utf-8")
		return 0

	result, message = edit_text("kept", argv=["ed"], runner=runner,
	                            tmpdir=str(tmp_path))
	assert result is None
	assert "could not be read" in message


# -- the text itself -------------------------------------------------------

@pytest.mark.parametrize("text", [
	"plain",
	"line one\nline two\n",
	"trailing spaces   \nand\ttabs\n",
	"広い文字 and emoji \U0001f600\n",
	"  leading indentation preserved\n",
	"final newline absent",
	"",
])
def test_text_makes_the_round_trip_byte_for_byte(tmp_path, text):
	"""Whitespace, newlines and Unicode are content. An editor round trip that
	quietly normalises them would rewrite the human's message."""
	seen = {}

	def runner(command):
		with open(command[-1], "r", encoding="utf-8", newline="") as fh:
			seen["seed"] = fh.read()
		return 0

	result, _ = edit_text(text, argv=["ed"], runner=runner, tmpdir=str(tmp_path))
	assert seen["seed"] == text, "the seed was altered on the way in"
	assert result == text, "the draft was altered on the way out"


def test_quote_prefixes_every_line_and_attributes_it():
	quoted = quote("first\n\nthird", "acme.reviewer", "2026-08-08T10:00:00Z")
	assert "On 2026-08-08T10:00:00Z, acme.reviewer wrote:" in quoted
	body = [line for line in quoted.splitlines() if line.startswith(">")]
	assert body == ["> first", ">", "> third"]
	# Room to write ABOVE the quote, which is where the reply goes.
	assert quoted.startswith("\n\n")


def test_quote_survives_hostile_text_without_interpreting_it():
	quoted = quote("vim: set nomodeline=0:\n\x1b[2J", "a.one", "now")
	assert "\x1b[2J" in quoted          # copied verbatim into the DRAFT...
	assert all(line.startswith(">") or not line.strip() or "wrote:" in line
	           for line in quoted.splitlines())


# -- the check/read window -------------------------------------------------

def test_a_same_size_replacement_is_refused(tmp_path):
	"""The inode check is what does the work here, not the size check: the
	replacement is byte-for-byte the same length as what we wrote, so a size
	comparison alone would wave it through."""
	def runner(command):
		path = command[-1]
		original = open(path).read()
		os.unlink(path)
		with open(path, "w") as fh:
			fh.write("X" * len(original))     # same size, different inode
		return 0

	result, message = edit_text("hello", argv=["ed"], runner=runner,
	                            tmpdir=str(tmp_path))
	assert result is None
	assert "replaced" in message


def test_nothing_looks_up_the_path_again_after_the_editor_returns(tmp_path, monkeypatch):
	"""The race this closes: verifying a PATH and then opening it is two
	lookups of the same name at two instants, and the name can be replaced in
	between -- the check passes on our file and the read gets the attacker's.

	Asserted as the absence of the second lookup, because that is the property
	rather than a guess at the attacker's timing: after the editor returns,
	the draft path is opened ONCE and never stat-ed by name. Everything else
	is decided about that descriptor.

	A first version of this test simulated a swap after `os.open` returned and
	passed against a path-then-open implementation too -- it was measuring the
	wrong window."""
	after_editor = {"running": False}
	opens, path_stats = [], []
	real_open, real_stat, real_lstat = os.open, os.stat, os.lstat

	def record_open(path, *args, **kwargs):
		if after_editor["running"] and isinstance(path, str):
			opens.append(path)
		return real_open(path, *args, **kwargs)

	def record_stat(path, *args, **kwargs):
		if after_editor["running"] and isinstance(path, str):
			path_stats.append(path)
		return real_stat(path, *args, **kwargs)

	def record_lstat(path, *args, **kwargs):
		if after_editor["running"] and isinstance(path, str):
			path_stats.append(path)
		return real_lstat(path, *args, **kwargs)

	def runner(command):
		with open(command[-1], "w") as fh:
			fh.write("what the human wrote")
		after_editor["running"] = True        # everything from here is suspect
		return 0

	monkeypatch.setattr(os, "open", record_open)
	monkeypatch.setattr(os, "stat", record_stat)
	monkeypatch.setattr(os, "lstat", record_lstat)
	result, _ = edit_text("seed", argv=["ed"], runner=runner, tmpdir=str(tmp_path))

	assert result == "what the human wrote"
	drafts = [p for p in opens if p.endswith(".md")]
	assert len(drafts) == 1, f"the draft path was opened {len(drafts)} times"
	assert not [p for p in path_stats if p.endswith(".md")], (
		f"the draft path was stat-ed by NAME after the editor returned: "
		f"{path_stats} -- that is the second lookup the swap races")


def test_the_baseline_comes_from_the_created_descriptor(tmp_path, monkeypatch):
	"""The window BEFORE the editor runs, which the post-editor pin does not
	cover.

	`mkstemp` hands back the authoritative descriptor. If the baseline is
	taken from the PATHNAME after that descriptor is closed, a replacement in
	between BECOMES the accepted baseline -- and the later check then agrees
	with the attacker's file and imports it.

	Simulated by swapping the pathname at the moment the creation descriptor
	is closed. Taking the baseline with `fstat` on that descriptor, before it
	closes, is what makes the swap detectable."""
	attacker = tmp_path / "attacker"
	attacker.write_text("attacker content")
	real_fdopen = os.fdopen
	swapped = {"done": False}

	def fdopen_then_swap(fd, *args, **kwargs):
		handle = real_fdopen(fd, *args, **kwargs)
		real_close = handle.close

		def close_and_swap():
			real_close()
			if not swapped["done"]:
				swapped["done"] = True
				for path in tmp_path.glob("baton-draft-*.md"):
					os.unlink(path)
					os.link(attacker, path)   # a DIFFERENT inode at that name
		handle.close = close_and_swap
		return handle

	monkeypatch.setattr(os, "fdopen", fdopen_then_swap)
	result, message = edit_text("seed", argv=["ed"], runner=lambda c: 0,
	                            tmpdir=str(tmp_path))
	assert swapped["done"], "the swap never happened; the test proved nothing"
	assert result is None, f"the attacker's file was imported: {result!r}"
	assert "replaced" in message


def test_a_successful_editor_that_changed_nothing_returns_the_seed(tmp_path):
	"""The raw fact the console has to cope with, stated where it happens.

	`:q!` in Vim exits ZERO and leaves the file untouched, and so does `:wq`
	over an unedited buffer. There is no failure here to detect: the exit
	status is success and the bytes come back identical. Any caller that
	treats "not None" as "the human wrote something" is wrong, and was --
	a cancelled full reply left the human in a provisional draft they had
	never written."""
	seen = []

	def runner(command):
		seen.append(command)
		return 0                          # opened the file, wrote nothing

	result, message = edit_text("the seed", argv=["ed"], runner=runner,
	                            tmpdir=str(tmp_path))
	assert seen, "the editor never ran"
	assert result == "the seed", "an unchanged file did not come back verbatim"
	assert result is not None, "this is NOT the failure path; that is the point"
	assert "imported" in message
