"""W8160 — human-facing TUI timestamps read in the operator's own time.

`work/records/2026/08/finding-tui-local-time/`.

THE DEFECT. The console painted canonical UTC fields verbatim. A Denver
terminal whose own clock said `2026-08-24 23:10` showed a Message stamped
`2026-08-25 00:36:19` — a FUTURE local time, with nothing on screen to say the
number was not local. An unlabelled wall clock is read as local, because that
is what a wall clock means, so the display was not merely inconvenient: it was
wrong in a way an operator could not detect.

THE RULING. Storage, the JSON API and every protocol value stay UTC and are
untouched. One shared presentation helper converts at the rendering boundary
through the host's ACTIVE timezone, and every full value carries the zone
abbreviation that decided it.

What these cases hold:

- the two input forms — explicit `Z`/offset instants and Baton's canonical
  naive-UTC Message spelling — reach the same instant, because attaching UTC
  before converting is the difference between a correct stamp and the original
  defect wearing a zone label;
- the zone is asked for at RENDER time, so the historical daylight rule for
  that instant decides (`MST` in January, `MDT` in July) and a `TZ` change
  under a live process is honoured;
- every absolute site the reviewer inventoried goes through it — Message
  reader and index, Event reader, index and claim interval, Poke table and
  detail, Teams pickup, runtime and last-answer;
- the elapsed cells (`Held`, `Since`, `Waiting`, fact age, phase duration) are
  timezone-invariant and are NOT touched; converting a duration as a wall
  clock would be a regression;
- the compact index columns MEASURE the zone-bearing value and drop whole
  under width pressure — a five-cell slice that removes the suffix recreates
  the exact ambiguity this ruling exists to remove;
- a UTC host keeps its wall-clock digits and gains a visible `UTC`;
- canonical JSON is byte-identical before and after the console renders.
"""

from __future__ import annotations

import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import (Console, duration_cell,         # noqa: E402
                                held_cell, local_stamp)
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402


DENVER = "America/Denver"
# One instant whose LOCAL calendar day is the previous one — the reported
# shape, and the only kind of case that can tell a conversion from a relabel.
CROSS_DAY = "2026-08-25T00:36:19Z"
CROSS_DAY_NAIVE = "2026-08-25 00:36:19"
CROSS_DAY_LOCAL = "2026-08-24 18:36:19 MDT"


@pytest.fixture()
def zone():
	"""Set the host timezone for one case and put libc back afterwards.

	BOTH levels: `os.environ` is what a child process inherits and
	`time.tzset()` is what this one's `localtime` reads. Restoring only
	the first would leave every later case in this worker converting
	through a zone it never asked for."""
	previous = os.environ.get("TZ")

	def use(name):
		os.environ["TZ"] = name
		time.tzset()

	yield use
	if previous is None:
		os.environ.pop("TZ", None)
	else:
		os.environ["TZ"] = previous
	time.tzset()


# -- the formatter itself ----------------------------------------------------

class TestOneInstantOneConversion:

	def test_an_explicit_utc_instant_becomes_the_local_wall_clock(self, zone):
		"""The reported shape: the local calendar day is the PREVIOUS
		one, which is what made the original display look like a future
		timestamp."""
		zone(DENVER)
		assert local_stamp(CROSS_DAY) == CROSS_DAY_LOCAL

	def test_the_canonical_naive_spelling_reaches_the_same_instant(
			self, zone):
		"""THE TRAP THIS RULING NAMES. Baton stores Message timestamps
		as UTC fields with no offset, which `fromisoformat` returns
		naive. `astimezone()` on that assumes the fields are already
		local: it would keep `00:36:19`, add `MDT`, and swear to a
		number six hours wrong. Attaching UTC first is what makes the
		two forms one instant."""
		zone(DENVER)
		assert local_stamp(CROSS_DAY_NAIVE) == local_stamp(CROSS_DAY)
		assert local_stamp(CROSS_DAY_NAIVE) == CROSS_DAY_LOCAL

	def test_an_offset_bearing_instant_is_honoured_not_assumed(self, zone):
		"""A value that already carries its own offset is converted FROM
		that offset, not reinterpreted."""
		zone(DENVER)
		assert local_stamp("2026-08-24T20:36:19+02:00") \
			== "2026-08-24 12:36:19 MDT"

	def test_fractional_seconds_parse_and_are_not_displayed(self, zone):
		"""The projection emits milliseconds; a console row is read by
		eye. The instant survives, the fraction is not painted."""
		zone(DENVER)
		assert local_stamp("2026-08-25T05:17:35.151Z") \
			== "2026-08-24 23:17:35 MDT"

	def test_the_compact_form_is_time_only_and_still_carries_the_zone(
			self, zone):
		"""The acceptance's second half: a compact display must have an
		equally visible local-time context. `18:36` alone is the defect
		in five characters."""
		zone(DENVER)
		assert local_stamp(CROSS_DAY, compact=True) == "18:36 MDT"

	def test_absence_is_empty_so_each_caller_keeps_its_own_spelling(self):
		for absent in (None, "", "   "):
			assert local_stamp(absent) == ""
			assert local_stamp(absent, compact=True) == ""

	def test_an_unparseable_value_is_returned_verbatim(self, zone):
		"""The console is not where a malformed projection instant
		should be discovered. Text that is visibly not a local stamp is
		a better report than a traceback over the operator's screen."""
		zone(DENVER)
		assert local_stamp("not an instant") == "not an instant"
		assert local_stamp("2026-13-45T99:99:99Z") == "2026-13-45T99:99:99Z"


class TestTheZoneIsAskedForAtRenderTime:

	def test_winter_reads_mst_and_summer_reads_mdt(self, zone):
		"""The daylight rule in force AT THAT INSTANT decides, so one
		host renders two different zone labels. A timezone object built
		once would answer for the wrong half of the year."""
		zone(DENVER)
		assert local_stamp("2026-01-15T12:00:00Z") \
			== "2026-01-15 05:00:00 MST"
		assert local_stamp("2026-07-15T12:00:00Z") \
			== "2026-07-15 06:00:00 MDT"

	def test_the_repeated_hour_stays_distinguishable_by_its_label(self, zone):
		"""Fall-back gives Denver two local `01:30`s. The digits cannot
		tell them apart; the zone can, which is a second reason the
		label is not decoration."""
		zone(DENVER)
		first = local_stamp("2026-11-01T07:30:00Z")
		second = local_stamp("2026-11-01T08:30:00Z")
		assert first == "2026-11-01 01:30:00 MDT"
		assert second == "2026-11-01 01:30:00 MST"
		assert first != second, "the repeated hour collapsed to one value"

	def test_changing_the_timezone_under_a_live_process_is_honoured(
			self, zone):
		"""Nothing is cached. The same call in one process answers for
		whichever zone the host is configured for NOW."""
		zone(DENVER)
		denver = local_stamp(CROSS_DAY)
		zone("Europe/Berlin")
		berlin = local_stamp(CROSS_DAY)
		zone("Pacific/Auckland")
		auckland = local_stamp(CROSS_DAY)
		assert denver == CROSS_DAY_LOCAL
		assert berlin.startswith("2026-08-25 02:36:19 ")
		assert auckland.startswith("2026-08-25 12:36:19 ")
		assert len({denver, berlin, auckland}) == 3

	def test_a_utc_host_keeps_its_digits_and_gains_the_label(self, zone):
		"""The regression guard for the deployment this was reported
		from NOT being everyone's. A UTC host's wall clock is unchanged;
		what it gains is the statement that it IS the wall clock."""
		zone("UTC")
		assert local_stamp(CROSS_DAY) == "2026-08-25 00:36:19 UTC"
		assert local_stamp(CROSS_DAY_NAIVE) == "2026-08-25 00:36:19 UTC"
		assert local_stamp(CROSS_DAY, compact=True) == "00:36 UTC"

	def test_a_nameless_zone_falls_back_to_the_numeric_offset(self, zone):
		"""`tzname()` is preferred because an abbreviation is what the
		operator's other windows say. A platform with no name for the
		zone must still say WHICH clock this is — dropping the context
		would restore the ambiguity."""
		zone("<+0545>-5:45")
		rendered = local_stamp(CROSS_DAY)
		assert rendered.startswith("2026-08-25 06:21:19 ")
		suffix = rendered.rsplit(" ", 1)[-1]
		assert suffix, "the zone context was dropped entirely"
		assert suffix in ("+0545", "<+0545>", "+05:45"), rendered


# -- elapsed cells are timezone-invariant and stay that way ------------------

class TestElapsedCellsAreNotClocks:

	def test_the_duration_helpers_are_untouched_by_the_timezone(self, zone):
		"""`Held`, `Waiting`, phase duration and fact age are ELAPSED
		values. Converting them as wall clocks would turn `02:15` into a
		time of day, which is the regression the inventory warned
		about."""
		zone(DENVER)
		denver_held = held_cell("2026-08-25T00:36:19Z", 1787617179.0)
		denver_for = duration_cell(135)
		zone("Pacific/Auckland")
		assert held_cell("2026-08-25T00:36:19Z", 1787617179.0) \
			== denver_held
		assert duration_cell(135) == denver_for
		assert ":" in denver_held and len(denver_held) == 5


# -- the world every surface case is painted from ----------------------------

@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the timestamped work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	tr.claim_work(store, born["work_id"], actor_team="lang", actor="ada")
	yield {"config": config_path, "database": database, "store": store,
	       "work": born["work_id"]}
	store.close()


class Screen:
	"""The painted grid, in the shape the console draws it."""

	def __init__(self, height=32, width=160):
		self.height = height
		self.width = width
		self.rows = {}

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def clrtoeol(self):
		pass

	def addnstr(self, y, x, text, n=None, *rest):
		row = self.rows.get(y, "")
		text = str(text) if n is None else str(text)[:n]
		row = row.ljust(x)
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def console(world, member="ada"):
	return Console(world["store"], "lang", member,
	               config_path=world["config"])


def detail(world, tab="messages", member="ada"):
	view = console(world, member)
	view.detail_work = world["work"]
	view.mode = "detail"
	view.detail_tab = tab
	return view


def detail_lines(view, height=32, width=160):
	screen = Screen(height, width)
	view._render_detail(screen, height, width)
	return [line for line in screen.lines() if line.strip()]


def painted(view, height=32, width=160):
	screen = Screen(height, width)
	view.render(screen)
	return [line for line in screen.lines() if line.strip()]


def message_page(world, member="ada"):
	"""The Thread page the console paints, read the way the console
	reads it — through the canonical projection, so these cases never
	assert against a shape the renderer does not receive."""
	threads = pj.work_threads(world["store"], world["work"],
	                          viewer_team="lang", viewer_member=member)
	return pj.thread(world["store"], threads["rows"][0]["id"],
	                 viewer_team="lang", viewer_member=member,
	                 newest=True, limit=20)["messages"]


def event_page(world):
	return pj.work_events(world["store"], world["work"])["events"]


def zone_of(text):
	"""Every zone label this suite's hosts can produce, found in a
	painted line."""
	return [label for label in ("MDT", "MST", "UTC", "CEST", "NZST")
	        if label in text]


# -- every inventoried surface -----------------------------------------------

class TestEverySurfaceReadsLocal:

	def test_the_message_reader_header_carries_the_local_instant(
			self, world, zone):
		zone(DENVER)
		view = detail(world, "messages")
		lines = detail_lines(view)
		# The reader shares its row with the index pane beside it, so
		# the header is FOUND rather than assumed to start the line.
		header = next((line for line in lines
		               if "#2 lang.ada " in line), None)
		assert header is not None, lines
		assert zone_of(header), \
			f"the reader header carries no zone: {header}"
		assert "2026-08-25T" not in header, \
			f"a canonical UTC instant reached the reader: {header}"

	def test_the_message_index_time_cell_carries_the_zone(self, world, zone):
		zone(DENVER)
		view = detail(world, "messages")
		message = message_page(world)[0]
		assert view._message_cells(message)["Time"] \
			== local_stamp(message["ts"], compact=True)
		assert zone_of(view._message_cells(message)["Time"]), \
			view._message_cells(message)
		assert any(zone_of(line) for line in detail_lines(view))

	def test_the_event_reader_and_its_claim_interval_read_local(
			self, world, zone):
		zone(DENVER)
		view = detail(world, "events")
		lines = detail_lines(view)
		claim_line = next((line for line in lines
		                   if "claim: lang.ada from E" in line), None)
		assert claim_line is not None, lines
		assert zone_of(claim_line), \
			f"the claim interval kept a UTC instant: {claim_line}"
		header = next((line for line in lines if "#3 claim " in line
		               or "#2 claim " in line), None)
		assert header is not None, lines
		assert zone_of(header), header

	def test_the_event_index_time_cell_carries_the_zone(self, world, zone):
		zone(DENVER)
		view = detail(world, "events")
		events = event_page(world)
		entry = events[0]
		columns = view._event_columns(160, view.event_time_width(events))
		row = view._event_row(entry, columns)
		assert local_stamp(entry["ts"], compact=True) in row, row
		assert zone_of(row), row

	def test_the_poke_table_and_detail_read_local(self, world, zone):
		zone(DENVER)
		seq = tr.poke(world["store"], actor_team="lang", actor="grace",
		              target="lang.ada", request="still on it?")["poke"]
		tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
		               state="working", explanation="mid-way")
		view = console(world)
		view.handle(ord("p"))
		lines = painted(view)
		row = next(line for line in lines if line.startswith(f"P{seq} "))
		assert zone_of(row), f"the Asked cell kept a UTC instant: {row}"
		asked = next(line for line in lines if "asked by lang.grace" in line)
		assert zone_of(asked), asked
		answered = next(line for line in lines if "answered working" in line)
		assert zone_of(answered), answered
		# `MDT` contains a `T`, so the guard against the canonical
		# spelling names the canonical spelling.
		assert "2026-08-25T" not in row, row

	def test_the_teams_member_runtime_and_answer_read_local(
			self, world, zone):
		zone(DENVER)
		tr.runtime_start(world["store"], actor_team="lang", actor="ada",
		                 incarnation="run-1", adapter="codex",
		                 provider="OpenAI", model="gpt-5.6",
		                 session="s-1")
		tr.runtime_state(world["store"], actor_team="lang", actor="ada",
		                 incarnation="run-1", state="working",
		                 work=world["work"])
		seq = tr.poke(world["store"], actor_team="lang", actor="grace",
		              target="lang.ada", request="alive?")["poke"]
		tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
		               state="working", explanation="yes")
		view = console(world)
		while view.tab != "teams":
			view.handle(ord("]"))
		# Tall enough to reach the last-answer section: the member
		# detail is a long key/value column and a short screen would
		# fail this case for want of rows rather than for want of a
		# zone.
		lines = painted(view, height=48)
		for label in ("Since", "Last contact", "Lease expires"):
			line = next((entry for entry in lines
			             if entry.strip().startswith(label)), None)
			assert line is not None, (label, lines)
			assert zone_of(line), f"{label} kept a UTC instant: {line}"
		said = next((line for line in lines
		             if line.strip().startswith("At ")), None)
		assert said is not None and zone_of(said), (said, lines)

	def test_the_pickup_since_row_reads_local(self, zone, tmp_path):
		"""A participant who owes a claim: the pickup section carries an
		absolute `Since` beside its elapsed `Waiting`, and only the
		first of the two is a clock."""
		zone(DENVER)
		config_path, database = fx.build_instance(
			str(tmp_path),
			{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
		store = bw.Authority(database)
		tr.create_work(store, team="lang", kind="bug", title="unclaimed",
		               origin="external-report",
		               classification="suspected-defect",
		               author="ada", body="b")
		view = Console(store, "lang", "ada", config_path=config_path)
		while view.tab != "teams":
			view.handle(ord("]"))
		lines = painted(view, height=48)
		since = next((line for line in lines
		              if line.strip().startswith("Since")), None)
		waiting = next((line for line in lines
		                if line.strip().startswith("Waiting")), None)
		assert since is not None and zone_of(since), (since, lines)
		assert waiting is not None, lines
		assert not zone_of(waiting), \
			f"an elapsed cell was converted as a clock: {waiting}"
		store.close()


# -- the responsive compact columns ------------------------------------------

class TestTheCompactColumnsKeepOrDropTheWholeCell:

	def test_the_message_time_column_is_measured_not_declared(
			self, world, zone):
		zone(DENVER)
		view = detail(world, "messages")
		messages = message_page(world)
		measured = view.message_time_width(messages)
		assert measured == len(local_stamp(messages[0]["ts"], compact=True))
		assert measured > 5, "the declared width was treated as a cap"
		columns = dict(view.message_columns(160, 3, 4, measured))
		assert columns["Time"] == measured

	def test_the_declared_width_is_a_floor_and_never_a_cap(self, world):
		"""An empty page still allocates its heading, and a page never
		shrinks the column below what it declared."""
		view = detail(world, "messages")
		assert view.message_time_width([]) == len("Time")
		assert dict(view.message_columns(160, 3))["Time"] == 5

	def test_the_whole_time_column_drops_before_it_is_clipped(
			self, world, zone):
		"""`Time` is first in the drop order and still leaves WHOLE.
		Losing the column is honest; losing its suffix is the original
		defect back in five characters."""
		zone(DENVER)
		view = detail(world, "messages")
		messages = message_page(world)
		measured = view.message_time_width(messages)
		wide = [name for name, _w in
		        view.message_columns(160, 3, 4, measured)]
		tight = [name for name, _w in
		         view.message_columns(24, 3, 4, measured)]
		assert "Time" in wide
		assert "Time" not in tight, tight
		for width in range(20, 60):
			kept = dict(view.message_columns(width, 3, 4, measured))
			assert kept.get("Time") in (None, measured), \
				f"a clipped Time cell survived at width {width}: {kept}"

	def test_the_event_time_column_and_its_pane_grow_together(
			self, world, zone):
		"""`EVENT_INDEX_WIDTH` sizes the pane the index is painted in.
		A measured `TIME` inside a pane sized from the DECLARED widths
		would be dropped at every terminal size — the pane would never
		offer it the cells."""
		zone(DENVER)
		view = detail(world, "events")
		events = event_page(world)
		measured = view.event_time_width(events)
		assert measured == len(local_stamp(events[0]["ts"], compact=True))
		assert measured > 5
		pane = view.event_index_width(events)
		assert pane == view.EVENT_INDEX_WIDTH - 5 + measured
		columns = dict(view._event_columns(pane, measured))
		assert columns["TIME"] == measured, columns

	def test_a_narrow_event_pane_drops_whole_columns_from_the_right(
			self, world, zone):
		zone(DENVER)
		view = detail(world, "events")
		events = event_page(world)
		measured = view.event_time_width(events)
		names = [name for name, _w in view._event_columns(24, measured)]
		assert "FOR" not in names and "PHASE" not in names, names
		for width in range(20, 70):
			kept = dict(view._event_columns(width, measured))
			assert kept.get("TIME") in (None, measured), \
				f"a clipped TIME cell survived at width {width}: {kept}"

	def test_the_painted_index_never_shows_a_bare_wall_clock(
			self, world, zone):
		"""The end-to-end statement of the same rule, on the real
		paint: at every width the Message index either shows a
		zone-bearing time or shows none at all."""
		zone(DENVER)
		bare = local_stamp(message_page(world)[0]["ts"],
		                   compact=True).split(" ")[0]
		for width in (60, 80, 110, 160):
			view = detail(world, "messages")
			lines = detail_lines(view, width=width)
			for line in lines:
				if bare in line:
					assert zone_of(line), \
						f"an unlabelled wall clock at {width}: {line}"


# -- canonical values are untouched ------------------------------------------

class TestCanonicalValuesStayUtc:

	@staticmethod
	def canonical(world):
		return json.dumps(
			{"detail": pj.detail(world["store"], world["work"],
			                     viewer_team="lang",
			                     viewer_member="ada"),
			 "messages": message_page(world),
			 "events": event_page(world)},
			sort_keys=True, default=str)

	def test_the_canonical_page_is_byte_identical_across_rendering(
			self, world, zone):
		"""The patch boundary, asserted rather than promised. The store
		and the projection are not part of this ruling, and the host
		timezone must not reach either."""
		zone("UTC")
		before = self.canonical(world)
		zone(DENVER)
		detail_lines(detail(world, "messages"))
		detail_lines(detail(world, "events"))
		after = self.canonical(world)
		assert before == after
		assert "MDT" not in after and "MST" not in after

	def test_the_projection_still_speaks_utc_under_a_non_utc_host(
			self, world, zone):
		zone(DENVER)
		stamp = message_page(world)[0]["ts"]
		assert not zone_of(stamp), stamp
		assert local_stamp(stamp) != stamp
		events = event_page(world)
		assert all(entry["ts"].endswith("Z") or " " in entry["ts"]
		           for entry in events)
		assert all(not zone_of(entry["ts"]) for entry in events)


# -- the real terminal -------------------------------------------------------

def open_detail_on_a_terminal(world, viewer="lang.ada"):
	"""Drive the real console to the claimed Work's Messages page.

	The child inherits `TZ` from this process, which is the whole point:
	the conversion has to happen in a curses process nobody handed a
	timezone to explicitly."""
	text, status, steps = ptyharness.drive(world["config"], viewer, [
		(b"\r", 0.8),                 # the claimed Work's detail
		(b"qy", 0.4),
	], columns=160, lines=32)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
	return ptyharness.replay(steps[0], columns=160, lines=32)


def test_a_non_utc_real_terminal_converts_rather_than_relabels(world, zone):
	"""Through curses, on a pty, with the host configured for the zone
	this defect was reported from.

	The assertion is the EXACT expected local rendering of the canonical
	value, computed here from the store. A case that only looked for
	`MDT` would pass on a console that appended a label to an unchanged
	UTC number, which is precisely the failure mode worth catching."""
	zone(DENVER)
	expected = local_stamp(message_page(world)[0]["ts"])
	screen = open_detail_on_a_terminal(world)
	assert any(expected in line for line in screen), (expected, screen[:16])


def test_a_real_terminal_shows_the_local_calendar_day_when_it_differs(
		world, zone):
	"""The reported shape, on a real terminal: a local calendar day that
	is NOT the UTC one.

	Which zone produces that depends on the hour this suite runs, so the
	zone is CHOSEN from the instant rather than assumed — a fixed zone
	would make this case prove the cross-day rule only for part of the
	day and silently prove nothing for the rest."""
	import datetime as dt

	stamp = message_page(world)[0]["ts"]
	utc_day = dt.datetime.fromisoformat(
		stamp.replace("Z", "+00:00").replace(" ", "T")).replace(
			tzinfo=dt.timezone.utc).date().isoformat()
	for candidate in ("Pacific/Midway", "Pacific/Kiritimati"):
		zone(candidate)
		expected = local_stamp(stamp)
		if expected.split(" ")[0] != utc_day:
			break
	else:                                   # pragma: no cover - unreachable
		raise AssertionError(
			f"neither UTC-11 nor UTC+14 crosses the day at {stamp}")
	screen = open_detail_on_a_terminal(world)
	assert any(expected in line for line in screen), (expected, screen[:16])
	assert not any(utc_day in line and expected not in line
	               for line in screen), \
		f"the UTC calendar day survived on screen: {utc_day}"
