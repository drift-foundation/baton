"""W81: bold Title is viewer-personal actionability.

The superseding ruling (finding-tui-hot-cue-live-visibility): bold
answers "what am I supposed to handle?" — reserved for Work the CURRENT
VIEWER can act on: they hold its active claim; or it is open, ready,
unclaimed, not blocked/parked, and its Route endpoint resolves to
them (every eligible handler of a multi-handler Route until one
claims; only the winner after); or they carry an unresolved directed
`@` obligation on it (independently actionable even while blocked).
Everyone else's activity stays visible through Phase, Handler, and
the Held timer; the three-tick Phase-change blink stays an observed-change
cue, not an ownership cue. Presentation only — no authority mutation,
no authorization change.
"""

from __future__ import annotations

import curses
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console, actionable_work       # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	# ada AND grace both hold the default role, but the fixture route
	# resolves handlers=[ada] only — grace is a configured member who
	# is NOT a resolved Route handler, exactly the contrast the
	# ruling distinguishes.
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title="w", team="lang", author="ada"):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b")


def row_for(world, work_id, viewer_team="lang", viewer_member="ada"):
	# detail shares the tree's row builder — the same canonical facts,
	# but visible across team boundaries for the cross-team assertions.
	return pj.detail(world["store"], work_id, viewer_team=viewer_team,
	                 viewer_member=viewer_member)


def test_the_actionability_matrix(world):
	"""Every ruled branch over real projections: claim ownership,
	resolved-Current readiness, the directed @, and every exclusion
	(blocked, parked, closed, foreign claimant, unresolved member,
	other team)."""
	store = world["store"]
	work = make(world, "the subject")["work_id"]
	# open, ready, unclaimed, Current resolves to ada: actionable for
	# ada — NOT for grace (configured member, unresolved handler) and
	# NOT for push.sl (another team)
	assert actionable_work(row_for(world, work), "lang", "ada")
	assert not actionable_work(
		row_for(world, work, viewer_member="grace"), "lang", "grace")
	assert not actionable_work(
		row_for(world, work, "push", "sl"), "push", "sl")
	# after ada claims: only the claimant keeps the cue
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert actionable_work(row_for(world, work), "lang", "ada")
	assert not actionable_work(
		row_for(world, work, viewer_member="grace"), "lang", "grace")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", episode=fx.episode_of(store, work),
	                 reason="cycling")
	# blocked: ready=false — the arrow explains, bold does not
	gate = make(world, "the gate")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	blocked = row_for(world, work)
	assert not blocked["ready"]
	assert not actionable_work(blocked, "lang", "ada")
	tr.close_work(store, gate, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	# blocked and parked: not bold even though the Route names the viewer
	second_gate = make(world, "second gate")["work_id"]
	tr.add_dependency(store, work, second_gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	assert not actionable_work(row_for(world, work), "lang", "ada")
	tr.close_work(store, second_gate, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	parked = make(world, "parked row")["work_id"]
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert not actionable_work(row_for(world, parked), "lang", "ada")
	# terminal: never bold
	done = make(world, "finished")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	closed = row_for(world, done)
	assert closed["status"] == "closed"
	assert not actionable_work(closed, "lang", "ada")


def test_a_directed_obligation_is_independently_actionable(world):
	"""An unresolved @ on the Work bolds it for the obligated viewer —
	even while dependency-blocked — and resolves away with the
	response."""
	store = world["store"]
	born = make(world, "asked", team="push", author="sl")
	work, thread = born["work_id"], born["thread"]
	gate = make(world, "asker gate", team="push", author="sl")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="push", actor="sl", rationale="test dependency")
	asked = tr.post_thread(store, thread, author_team="push",
	                       author="sl", body="lang: confirm?",
	                       request="lang.bug", wait=False, on=work)
	blocked = row_for(world, work)
	assert not blocked["ready"], "the block did not gate readiness"
	assert blocked["my_pending_obligations"] > 0
	assert actionable_work(blocked, "lang", "ada"), \
		"a directed @ lost its independent actionability while blocked"
	assert not actionable_work(
		row_for(world, work, "push", "sl"), "push", "sl"), \
		"the asker inherited the responder's cue"
	tr.respond_obligation(store, asked["seq"], team="lang",
	                      member="ada", body="confirmed")
	assert not actionable_work(row_for(world, work), "lang", "ada"), \
		"a resolved obligation kept its bold"


def test_two_viewers_see_two_bold_sets(world):
	"""The same authority, two consoles: each viewer's bold set is
	their own. mine (claimed by ada) bolds only for ada; the ready
	unclaimed row whose Current resolves to ada bolds for ada alone;
	grace keeps activity visibility without bold."""
	store = world["store"]
	mine = make(world, "mine claimed")["work_id"]
	tr.claim_work(store, mine, actor_team="lang", actor="ada")
	ready = make(world, "ready for ada")["work_id"]

	class Screen:
		def __init__(self):
			self.calls = []

		def addnstr(self, y, x, text, *rest):
			attr = rest[1] if len(rest) > 1 else 0
			self.calls.append((str(text), attr))

	def bold_titles(member):
		console = Console(store, "lang", member,
		                  config_path=world["config"])
		screen = Screen()
		console._render_table(screen, 24, 110, console.rows())
		return {text.strip() for text, attr in screen.calls
		        if attr & curses.A_BOLD}

	ada_bold = bold_titles("ada")
	# W2938: the Title truncates three cells earlier, so the bold set
	# carries drawn PREFIXES — the property is which rows are bold, not
	# how many characters of their titles survive the layout.
	def bolded(title):
		return any(text and title.startswith(text) for text in ada_bold)

	assert bolded("mine claimed")
	assert bolded("ready for ada")
	grace_bold = bold_titles("grace")
	assert grace_bold == set(), \
		f"grace inherited someone else's cue: {grace_bold}"


def test_the_cue_is_a_pure_fact_projection(world):
	"""JSON/TUI parity: the painted bold set equals the predicate
	recomputed from the canonical rows alone — the terminal invents
	nothing and reads nothing extra."""
	store = world["store"]
	claimed = make(world, "parity claimed")["work_id"]
	tr.claim_work(store, claimed, actor_team="lang", actor="ada")
	make(world, "parity ready")
	blocked = make(world, "parity blocked")["work_id"]
	tr.add_dependency(store, blocked, claimed, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	rows = pj.tree(store, viewer_team="lang",
	               viewer_member="ada")["rows"]
	expected = {row["title"] for row in rows
	            if actionable_work(row, "lang", "ada")}

	class Screen:
		def __init__(self):
			self.calls = []

		def addnstr(self, y, x, text, *rest):
			attr = rest[1] if len(rest) > 1 else 0
			self.calls.append((str(text), attr))

	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	screen = Screen()
	# W93 added a conditional Agent column, so at 110 the Title — the
	# one column the layout may truncate — is narrower whenever the
	# window holds claimed Work, as this one does. The property under
	# test is WHICH rows are bold, not how many characters of their
	# titles fit, so the comparison is on the painted prefix.
	console._render_table(screen, 24, 110, rows)
	painted = {text.strip() for text, attr in screen.calls
	           if attr & curses.A_BOLD}
	assert {title[:10] for title in painted} == \
		{title[:10] for title in expected}, (painted, expected)
	assert "parity blocked" not in painted


def test_personal_bold_on_the_real_terminal_wide_and_narrow(tmp_path):
	"""PTY: the viewer's actionable titles carry the bold SGR at full
	width AND at a narrow width (the Title is never dropped); the
	non-actionable row never does."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	mine = tr.create_work(store, team="lang", kind="bug",
	                      title="mine-to-do", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	tr.claim_work(store, mine, actor_team="lang", actor="ada")
	other = tr.create_work(store, team="lang", kind="bug",
	                       title="not-mine", origin="external-report",
	                       classification="suspected-defect",
	                       author="ada", body="b")["work_id"]
	tr.add_dependency(store, other, mine, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	store.close()
	BOLD = (r"\x1b\[(?:\d+;)*0?1(?:;\d+)*m"
	        r"(?:\x1b\[[0-9;?]*[A-Za-z])*")
	for columns, lines in ((110, 32), (46, 24)):
		text, status, steps = ptyharness.drive(config, "lang.ada", [
			(b"", 0.6), (b"qy", 0.4)], columns=columns, lines=lines)
		assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
		assert re.search(BOLD + "mine-to-do", steps[0]), \
			f"no personal bold at {columns} columns"
		assert not re.search(BOLD + "not-mine", steps[0]), \
			f"a non-actionable title went bold at {columns} columns"


def test_two_eligible_handlers_bold_until_one_claims(tmp_path):
	"""R1: a TRUE multi-handler Current — both resolved handlers'
	consoles bold the ready unclaimed row; after one wins the claim,
	only the winner keeps the cue while the loser still sees the
	activity through Age; the configured-but-unresolved member stays
	the ineligible negative throughout."""
	import json as _json
	from baton_work import lifecycle as lc
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"],
		                      "grace": ["obs"]},
		          "kinds": ["bug"]}})
	# the route resolves TWO handlers; grace stays configured but
	# unresolved — the ruling's ineligible negative
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	try:
		work = tr.create_work(store, team="lang", kind="bug",
		                      title="shared duty",
		                      origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="b")["work_id"]

		def actionable(member):
			return actionable_work(
				pj.detail(store, work, viewer_team="lang",
				          viewer_member=member), "lang", member)

		assert actionable("ada") and actionable("bee"), \
			"an eligible handler lost the pre-claim cue"
		assert not actionable("grace"), \
			"the unresolved member gained the cue"
		# bee wins the claim: only the winner keeps bold
		tr.claim_work(store, work, actor_team="lang", actor="bee")
		assert actionable("bee")
		assert not actionable("ada"), \
			"the losing handler kept the execution cue after the claim"
		assert not actionable("grace")
		# the loser still reads the activity: claimant + age facts live
		view = pj.detail(store, work, viewer_team="lang",
		                 viewer_member="ada")
		assert view["handler"] == {"team": "lang", "member": "bee",
	                   "participant": "lang.bee"}
		assert view["claimed_at"] is not None
	finally:
		store.close()
