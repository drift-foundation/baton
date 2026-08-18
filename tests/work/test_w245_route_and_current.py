"""W245 (finding-current-is-claimant): Route is eligibility, Current is
the claimant.

The live trial produced both failure directions from ONE ambiguity. W104
showed a Current worker (`baton.impl`) while nobody had claimed it, so a
routed handoff awaiting pickup read as staffed. W101 showed the inverse:
a live claimant while the Work was blocked, with the route unable to say
whether anybody was executing.

The old projection published the routing endpoint as `current` and the
claimant as `active`. These are the checks that keep the two questions
apart — WHO MAY CLAIM, and WHO IS EXECUTING — including that no
compatibility alias survives to reintroduce the ambiguity.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def store(tmp_path):
	"""Two handlers on the implementation route, so eligibility is
	genuinely broader than any one claimant."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl", "rview", "ops"],
		                      "bee": ["impl"]},
		          "kinds": ["bug"]}})
	team = document["teams"]["lang"]
	team["routes"] = {
		"build": {"role": "impl", "handlers": ["ada", "bee"]},
		"review": {"role": "rview", "handlers": ["ada"]},
	}
	team["kinds"] = {
		"bug": {"display": "Bug", "route": "build"},
		"rev": {"display": "Rev", "route": "review"},
	}
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	with bw.Authority(result["database"]) as authority:
		authority.test_config_path = config_path
		authority.test_database = result["database"]
		yield authority


def _create(store, title="claimable", kind="bug"):
	return tr.create_work(store, team="lang", kind=kind, title=title,
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")["work_id"]


def _view(store, work, member="ada"):
	return pj.detail(store, work, viewer_team="lang", viewer_member=member)


# -- the two questions, kept apart ------------------------------------------

def test_a_routed_handoff_awaiting_pickup_projects_no_current(store):
	"""The exact W104 trial failure: routed, eligible, nobody executing.
	Current must be NULL, or the board claims a worker that does not
	exist."""
	work = _create(store)
	view = _view(store, work)
	assert view["route"]["endpoint"] == "lang.bug"
	assert view["handler"] is None, \
		"unclaimed Work projected a current participant"


def test_only_a_successful_claim_populates_current(store):
	work = _create(store)
	assert _view(store, work)["handler"] is None
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	view = _view(store, work)
	assert view["handler"] == {"team": "lang", "member": "bee",
	                           "participant": "lang.bee"}
	# eligibility is untouched by who happened to win it
	assert view["route"]["endpoint"] == "lang.bug"
	assert sorted(view["route"]["handlers"]) == ["ada", "bee"]


def test_release_clears_current_and_leaves_the_route_alone(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="handing back")
	view = _view(store, work)
	assert view["handler"] is None
	assert view["route"]["endpoint"] == "lang.bug", \
		"releasing a claim rerouted the Work"


def test_a_pass_moves_route_and_leaves_the_recipient_unclaimed(store):
	"""The handoff contract, in the new names: route and phase move,
	current clears, and nobody is claimed on the recipient's behalf."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over to review")
	view = _view(store, work)
	assert view["route"]["endpoint"] == "lang.rev"
	assert view["phase"] == "queued"
	assert view["handler"] is None, \
		"the pass claimed the Work for its recipient"


def test_parking_leaves_no_current(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert _view(store, work)["handler"] is None, \
		"parked Work still names an executing participant"


def test_waiting_on_gates_leaves_no_current(store):
	"""A gate wait needs a real open gate, so the blocker is created
	first — the point being that entering the wait releases the claim."""
	work = _create(store)
	blocker = _create(store, title="gate")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="reopened below", outcome="satisfying")
	second = _create(store, title="gate two")
	tr.add_dependency(store, work, second, actor_team="lang",
	                  actor="ada", rationale="live gate")
	assert _view(store, work)["handler"] is None, \
		"waiting Work still names an executing participant"


def test_blocked_work_keeps_its_route_and_names_no_current(store):
	work = _create(store)
	blocker = _create(store, title="gate")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	view = _view(store, work)
	assert view["ready"] is False
	assert view["route"]["endpoint"] == "lang.bug", \
		"a dependency rewrote the route"
	assert view["handler"] is None


def test_a_terminal_close_names_no_current(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	view = _view(store, work)
	assert view["status"] == "closed"
	assert view["handler"] is None, "closed Work still named an executor"


# -- authorization still resolves from the route ----------------------------

def test_authorization_resolves_from_route_not_from_the_claimant(store):
	"""A claimant's identity must never widen or narrow who MAY act;
	that is the route's job, and conflating them is how a display name
	becomes an authorization decision."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	# bee is eligible by route, but ada holds the claim: the competing
	# claim fails on the CLAIM, not on eligibility
	with pytest.raises(bw.WorkError, match="claimed by lang.ada"):
		tr.claim_work(store, work, actor_team="lang", actor="bee")
	# and a non-handler is refused for a different reason entirely
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="free it")
	assert _view(store, work)["handler"] is None


def test_a_claim_race_produces_exactly_one_current(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = store.last_seq()
	with pytest.raises(bw.WorkError):
		tr.claim_work(store, work, actor_team="lang", actor="bee")
	assert store.last_seq() == before, "the losing claim burned an event"
	assert _view(store, work)["handler"]["member"] == "ada"


# -- no alias survives ------------------------------------------------------

def test_no_compatibility_alias_remains(store):
	"""The finding is explicit: two names for one fact preserved the
	ambiguity, so `active` must be GONE rather than deprecated."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	view = _view(store, work)
	assert "active" not in view, \
		"the retired `active` alias is still published"
	rows = pj.tree(store, viewer_team="lang", viewer_member="ada")["rows"]
	assert all("active" not in row for row in rows)


def test_a_pinned_older_projection_refuses_rather_than_misreading(store):
	"""W245 reuses the `current` FIELD NAME for a different meaning, so
	a 7.x consumer would take an endpoint struct for a claimant and be
	confidently wrong. The major bump makes that refuse instead."""
	from baton_work import jsonapi
	assert jsonapi.PROJECTION_VERSION == "11.0"
	jsonapi.require_version("11.0")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("8.0")


def test_a_stale_consumer_cannot_read_route_membership_as_execution(store):
	"""The regression this finding exists to prevent: a consumer that
	treats "the route resolves to me" as "I am executing it". The two
	fields now disagree by construction on unclaimed Work."""
	work = _create(store)
	view = _view(store, work)
	eligible = "ada" in (view["route"]["handlers"] or ())
	executing = view["handler"] is not None
	assert eligible and not executing, \
		"eligibility and execution are no longer distinguishable"


# -- storage, events, readiness, restart ------------------------------------

def test_storage_names_the_two_facts_separately(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	row = store.conn.execute(
		"SELECT route_team, route_kind, handler_team, handler_member "
		"FROM work WHERE id=?", (work,)).fetchone()
	assert (row["route_team"], row["route_kind"]) == ("lang", "bug")
	assert (row["handler_team"], row["handler_member"]) == ("lang", "bee")


def test_close_evidence_records_the_route_it_closed_from(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	result = tr.close_work(store, work, actor_team="lang", actor="ada",
	                       rationale="done", outcome="satisfying")
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["payload"]["was_route_kind"] == "bug"
	assert "was_current_kind" not in event["payload"], \
		"close evidence still uses the ambiguous old name"


def test_readiness_reports_claimed_from_the_claimant(store):
	work = _create(store)
	def actionable():
		view = pj.wait_actionable(store, viewer_team="lang",
		                          viewer_member="ada",
		                          timeout_seconds=0)
		return next(a for a in view["actionable"] if a.get("work") == work)
	assert actionable()["claimed"] is False
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert actionable()["claimed"] is True


def test_the_split_survives_a_restart(store):
	"""A reopened authority must report the same two facts; the claim
	is durable state, not process memory."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	database = store.test_database
	store.conn.commit()
	with bw.Authority(database) as reopened:
		view = pj.detail(reopened, work, viewer_team="lang",
		                 viewer_member="ada")
		assert view["handler"] == {"team": "lang", "member": "bee",
		                           "participant": "lang.bee"}
		assert view["route"]["endpoint"] == "lang.bug"


def test_current_filter_can_name_a_claimant_retired_by_a_later_config(store):
	"""A config generation may change route eligibility without rewriting
	the exact identity captured by a live claim. That durable Current must
	remain queryable even after the participant is no longer a live member."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	with open(store.test_config_path, encoding="utf-8") as handle:
		document = _json.load(handle)
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["bee"]
	document["teams"]["lang"]["routes"]["build"]["handlers"] = ["ada"]
	with open(store.test_config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(store.test_config_path, actor="lang.ada")

	view = _view(store, work)
	assert view["handler"]["participant"] == "lang.bee"
	filtered = pj.home(store, viewer_team="lang", viewer_member="ada",
	                   work_filter={"handler": "lang.bee"})
	assert [row["id"] for row in filtered["rows"]] == [work]


# -- the vocabulary itself, so it cannot regress silently --------------------

_PROTOCOL_SOURCE = ("authority.py", "transitions.py", "projection.py",
                    "cli.py", "jsonapi.py", "lifecycle.py",
                    os.path.join("tui", "app.py"))

# Phrases where `current` denotes ELIGIBILITY. Every one is a claim about
# who MAY act, which is the Route's job — and three review rounds were
# spent finding them by eye, each time after a confident "they are all
# gone".
#
# COMPOSED rather than written out, so no forbidden phrase appears
# literally in this file and the scan can therefore cover its own source
# and the rest of the suite without matching itself. Spelling them out
# here would either self-trip the guard or force an exclusion that
# quietly stops protecting this file.
_ROUTE_MEANING = tuple(
	f"{case} {noun}"
	for case in ("current", "Current")
	for noun in ("handler", "endpoint", "route")
) + ("destination " + "Current", "provider " + "Current",
     "provider" + "_current")


def _sources():
	"""Protocol source AND the executable specifications. The tests are
	durable maintenance evidence: a docstring that says Current where the
	Route authorizes an act teaches the next maintainer the wrong rule
	just as effectively as a comment in the product."""
	root = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	product = os.path.join(root, "src", "baton_work")
	for name in _PROTOCOL_SOURCE:
		path = os.path.join(product, name)
		with open(path, encoding="utf-8") as handle:
			yield os.path.join("src", name), handle.read()
	suite = os.path.join(root, "tests", "work")
	for base, _dirs, files in os.walk(suite):
		for name in sorted(files):
			if not name.endswith(".py"):
				continue
			path = os.path.join(base, name)
			with open(path, encoding="utf-8") as handle:
				yield os.path.relpath(path, root), handle.read()


def test_protocol_source_never_says_current_to_mean_route():
	"""W245 R2/R3: comments, docstrings, help text, refusal strings, and
	test assertion messages all teach the authorization boundary. Pairing
	`current` with an eligibility noun where the ROUTE authorizes the act
	teaches the wrong rule — and the classify/create strings are
	user-facing, so it teaches it to operators too.

	This scan covers its own file, which is why the forbidden phrases are
	composed above rather than spelled out anywhere here."""
	offenders = []
	for name, body in _sources():
		for number, line in enumerate(body.splitlines(), 1):
			for phrase in _ROUTE_MEANING:
				if phrase in line:
					offenders.append(f"{name}:{number}: {line.strip()}")
	assert not offenders, (
		"`current` is used to mean route eligibility in:\n  "
		+ "\n  ".join(offenders))


def test_the_user_facing_help_names_route_authority():
	"""The specific strings an operator reads. classify is authorized by
	the resolved Route handler — NOT necessarily the exact claimant — so
	naming Current there actively teaches the wrong authority."""
	from baton_work import cli
	classify = cli.GRAMMAR["classify"]["help"]
	assert "Route handler" in classify, classify
	assert not any(phrase in classify for phrase in _ROUTE_MEANING), \
		classify
