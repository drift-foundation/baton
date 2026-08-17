"""W176 (finding-message-pane-header-redundancy): the split message
panes identify their ROLES, never content already visible elsewhere.

Acceptance, pinned on the virtual screen: distinct Thread /
Messages-list / selected-Message headings at wide and narrow widths;
exactly one blank separator row beneath the Thread list; long and
wide-character subjects contained in their Thread row; selection
moving list highlight and reader heading/body together; honest counts
for one- and multi-message threads with no duplicated identifiers.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(
	not hasattr(__import__("pty"), "fork"), reason="no pty support")

LONG_SUBJECT = ("a long subject that would previously reach the shared "
                "message heading truncated")           # 78 bytes: max-ish
WIDE_SUBJECT = "宽字符主题行进入线程列表但绝不进入下方标题"  # wide cells, <=80 bytes


def _world(tmp_path, extra_messages=0):
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the pane rig",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="opener")
	for index in range(extra_messages):
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body=f"reply number {index + 1}")
	store.close()
	return config_path, born


def _screen(config_path, script, columns=110, lines=32):
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", script, columns=columns, lines=lines)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, \
		text[-400:]
	return [ptyharness.replay(step, columns=columns, lines=lines)
	        for step in steps]


def test_wide_regions_are_distinct_and_separated_by_one_blank_row(tmp_path):
	config_path, _born = _world(tmp_path, extra_messages=1)
	screens = _screen(config_path, [(b"\r", 0.6), (b"qy", 0.4)])
	rows = screens[0]
	threads_at = next(index for index, line in enumerate(rows)
	                  if "Threads (" in line)
	messages_at = next(index for index, line in enumerate(rows)
	                   if "Messages (" in line)
	# The three headings are distinct regions on one screen.
	joined = "\n".join(rows)
	assert "Threads (1)" in joined
	assert "Messages (2)" in joined
	assert "Message M" in joined
	assert "Msgs —" not in joined and "»M" not in joined.replace(
		"»Message M", ""), "a content-repeating heading survived"
	# Exactly ONE blank separator row between the last thread row and
	# the Messages heading.
	between = rows[threads_at + 1:messages_at]
	blanks = [line for line in between if not line.strip()]
	assert len(blanks) == 1, \
		f"expected one blank separator, saw {len(blanks)}: {between!r}"
	assert not between[-1].strip(), \
		"the blank row does not sit directly above the lower panes"


def test_long_and_wide_subjects_stay_in_their_thread_row(tmp_path):
	config_path, born = _world(tmp_path)
	store = bw.Authority(
		os.path.join(os.path.dirname(config_path), "work.sqlite3"))
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 body="long-thread opener", labels=[born["work_id"]],
	                 subject=LONG_SUBJECT)
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 body="wide-thread opener", labels=[born["work_id"]],
	                 subject=WIDE_SUBJECT)
	store.close()
	screens = _screen(config_path, [
		(b"\r", 0.6), (b"j", 0.5), (b"j", 0.5), (b"qy", 0.4)])
	for screen in screens[1:3]:
		rows = screen
		messages_at = next(index for index, line in enumerate(rows)
		                   if "Messages (" in line)
		lower = "\n".join(rows[messages_at:])
		assert "subject that" not in lower and \
			"宽字符" not in lower, \
			"a subject leaked into the lower pane headings"
		assert "Messages (1)" in lower
		assert "Message M" in lower


def test_selection_moves_list_highlight_and_reader_together(tmp_path):
	config_path, _born = _world(tmp_path, extra_messages=2)
	screens = _screen(config_path, [
		(b"\r", 0.6),
		(b"\x17j", 0.4),              # focus the Message index
		(b"j", 0.5),                  # move the selection
		(b"qy", 0.4)])
	before = "\n".join(screens[1])
	after = "\n".join(screens[2])
	def reader_id(flat):
		for line in flat.splitlines():
			if "Message M" in line:
				return line.split("Message M")[1].split()[0]
		raise AssertionError("no reader heading")
	assert reader_id(before) != reader_id(after), \
		"selection did not change the reader heading"
	assert "reply number" in after, \
		"the reader body did not follow the selection"


def test_narrow_stack_keeps_role_labels_and_counts(tmp_path):
	config_path, _born = _world(tmp_path, extra_messages=2)
	screens = _screen(config_path, [(b"\r", 0.8), (b"qy", 0.4)],
	                  columns=60, lines=24)
	joined = "\n".join(screens[0])
	assert "Messages (3)" in joined, joined[:600]
	assert "Message M" in joined
	assert "Msgs —" not in joined
	rows = screens[0]
	threads_at = next(index for index, line in enumerate(rows)
	                  if "Threads (" in line)
	messages_at = next(index for index, line in enumerate(rows)
	                   if "Messages (" in line)
	blanks = [line for line in rows[threads_at + 1:messages_at]
	          if not line.strip()]
	assert len(blanks) == 1, "the narrow stack lost the one separator"


def test_an_empty_projected_page_keeps_honest_role_labels(tmp_path):
	"""The authority never creates an empty Thread, but a bounded reader
	still has an explicit empty-page branch. Its labels remain roles with an
	honest zero count and no invented selected-message identity."""
	from baton_work.tui.app import Console

	config_path, born = _world(tmp_path)
	store = bw.Authority(
		os.path.join(os.path.dirname(config_path), "work.sqlite3"))
	console = Console(store, "lang", "ada", config_path=config_path)
	console._cached = lambda _key, _read: {
		"messages": [], "next_after": None,
		"subject": "must not leak into a pane heading"}
	painted = []

	class Screen:
		def addnstr(self, y, x, text, *_rest):
			painted.append((y, x, str(text)))

	console._render_message_region(
		Screen(), 5, 24, 110, {"id": born["thread"]})
	store.close()
	flat = "\n".join(text for _y, _x, text in painted)
	assert "Messages (0)" in flat
	assert "Message" in flat and "Message M" not in flat
	assert "(no messages on this page)" in flat
	assert "must not leak" not in flat
