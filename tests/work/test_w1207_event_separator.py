"""W1207: the Event reader separates its summary from its audit record.

`work/records/2026/08/finding-event-payload-visual-separation/`. The
reader put the complete raw JSON directly under the last typed
metadata row. `payload:` labelled it, but with no vertical gap the JSON
read as one more metadata field and the eye had to re-parse the block
to find where the human summary ended.

The ruling is one blank row, and spacing rather than a rule: a
horizontal line spends width the reader needs and depends on glyphs
some terminals draw badly.

Presentation only. These tests hold the separator at every shape the
reader can take — plain, metadata-rich, narrow, wrapped, scrolled —
and hold that the payload itself, the projection, and the read-only
boundary are untouched.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console, soft_wrap               # noqa: E402
import fixtures as fx                                          # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		          "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the audited work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	return {"store": store, "config": config_path,
	        "work": born["work_id"], "thread": born["thread"]}


def console(world):
	return Console(world["store"], "lang", "ada",
	               config_path=world["config"])


def events(world):
	return pj.work_events(world["store"], world["work"])["events"]


def lines_for(world, entry):
	return console(world)._event_lines(entry)


def separator_index(lines):
	"""The one blank row, which must sit immediately before the label."""
	blanks = [index for index, line in enumerate(lines)
	          if line.strip() == ""]
	label = lines.index("  payload:")
	return blanks, label


# -- the separator ------------------------------------------------------------

def test_one_blank_row_sits_immediately_before_the_payload(world):
	entry = events(world)[0]
	lines = lines_for(world, entry)
	blanks, label = separator_index(lines)
	assert blanks == [label - 1], (blanks, label, lines)


def test_a_metadata_rich_event_still_has_exactly_one(world):
	"""Related Works, a claim interval, typed payload labels and refs
	all add rows between the header and the payload; the separator is
	after the LAST of them, once."""
	tr.claim_work(world["store"], world["work"], actor_team="lang",
	              actor="ada")
	tr.pass_work(world["store"], world["work"], actor_team="lang",
	             actor="ada", to="lang.rsrch",
	             comment="a comment that becomes a typed label")
	rich = [entry for entry in events(world)
	        if entry["kind"] in ("pass", "claim")]
	assert rich, [entry["kind"] for entry in events(world)]
	for entry in rich:
		lines = lines_for(world, entry)
		blanks, label = separator_index(lines)
		assert blanks == [label - 1], (entry["kind"], blanks, label)
		assert label > 2, "the separator swallowed the typed metadata"


def test_every_event_this_authority_can_produce_has_exactly_one(world):
	tr.claim_work(world["store"], world["work"], actor_team="lang",
	              actor="ada")
	tr.post_thread(world["store"], world["thread"], author_team="lang",
	               author="ada", body="a message")
	tr.set_phase(world["store"], world["work"], actor_team="lang",
	             actor="ada", phase="parked",
	             reason="deliberately deferred")
	for entry in events(world):
		lines = lines_for(world, entry)
		blanks, label = separator_index(lines)
		assert blanks == [label - 1], (entry["kind"], lines)


# -- the payload itself is untouched ------------------------------------------

def test_the_payload_block_is_unchanged(world):
	entry = events(world)[0]
	lines = lines_for(world, entry)
	label = lines.index("  payload:")
	rendered = "\n".join(line[2:] for line in lines[label + 1:])
	assert json.loads(rendered) == entry["payload"], rendered
	# still two-space indented, still sorted, still complete
	assert lines[label + 1].startswith("  {")


def test_an_absent_payload_still_gets_its_separator(world):
	"""W48 keeps absent and falsy payloads distinct; the separator must
	not depend on which one this is."""
	view = console(world)
	for payload in ({}, None, [], 0, "", False):
		entry = dict(events(world)[0])
		entry["payload"] = payload
		lines = view._event_lines(entry)
		blanks, label = separator_index(lines)
		assert blanks == [label - 1], (payload, lines)
	stripped = dict(events(world)[0])
	stripped.pop("payload")
	lines = view._event_lines(stripped)
	blanks, label = separator_index(lines)
	assert blanks == [label - 1], lines


# -- narrow and wrapped -------------------------------------------------------

@pytest.mark.parametrize("width", [120, 80, 60, 40, 24, 12])
def test_wrapping_neither_multiplies_nor_erases_it(world, width):
	"""The LOGICAL separator survives wrapping: the visual row directly
	above `payload:` is blank at every width, and the one logical blank
	became exactly one visual row.

	Asserted that way rather than by counting every blank in the block,
	because at very narrow widths the wrapper itself can emit a blank
	piece — a JSON line whose continuation indent nearly fills the pane
	leaves an empty first piece. That is `soft_wrap`'s pre-existing
	behaviour under W48 and has nothing to do with this separator; a
	test that counted blanks would have been measuring it instead."""
	tr.claim_work(world["store"], world["work"], actor_team="lang",
	              actor="ada")
	tr.pass_work(world["store"], world["work"], actor_team="lang",
	             actor="ada", to="lang.rsrch",
	             comment="a deliberately long handoff comment that will "
	                     "wrap at every width this case tries")
	for entry in events(world):
		logical = lines_for(world, entry)
		assert logical.count("") == 1, (width, entry["kind"], logical)
		wrapped = []
		for line in logical:
			pieces = soft_wrap(line, width)
			if line == "":
				assert pieces == [""], (width, pieces)
			wrapped.extend(pieces)
		label = next(index for index, line in enumerate(wrapped)
		             if line.strip().startswith("payload:"))
		assert wrapped[label - 1].strip() == "", \
			(width, entry["kind"], wrapped[label - 3:label + 1])


def test_an_empty_logical_line_stays_exactly_one_visual_line():
	"""The property the separator rests on, asserted directly rather
	than inferred from the block around it."""
	for width in (8, 12, 40, 200):
		assert soft_wrap("", width) == [""]


# -- the reader stays honest --------------------------------------------------

def test_a_scrolled_reader_still_reports_its_clipping(world):
	view = console(world)
	entry = events(world)[0]

	class Screen:
		def __init__(self):
			self.rows = {}

		def addnstr(self, y, x, text, n, *rest):
			self.rows[y] = str(text)[:n]

	total = len(view._event_lines(entry))
	for skip in (0, 1, 2, total - 1):
		view.event_skip = skip
		screen = Screen()
		view._paint_event_reader(screen, 0, 3, 0, 100, entry)
		assert view.event_clipped is (skip + 3 - (1 if skip else 0)
		                              < total), (skip, view.event_clipped)
		if skip:
			assert screen.rows[0].startswith(f"E{entry['seq']} (cont.)")


def test_the_separator_is_presentation_and_writes_nothing(world):
	before = world["store"].last_seq()
	view = console(world)
	for entry in events(world):
		view._event_lines(entry)
	assert world["store"].last_seq() == before


def test_the_projection_is_unchanged(world):
	"""Nothing about the Event projection moved: the reader added a
	row, the ledger did not."""
	entry = events(world)[0]
	for field in ("seq", "kind", "actor", "ts", "roles", "payload"):
		assert field in entry, field
	assert "separator" not in entry
