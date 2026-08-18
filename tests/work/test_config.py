"""C1: the v11 configuration schema and loader.

One valid document, then every refusal class the authorization names —
strict parse, unknown fields at every level, grammar, displays, membership,
role assignment, route coherence, kind mapping, identity fields — each
refused WITH THE FIELD NAMED, and each proven load-bearing by mutating the
one valid document rather than by constructing strawmen.
"""

from __future__ import annotations

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import config as cfg                          # noqa: E402

UUID = "ab" * 16

VALID = {
	"config_version": 1,
	"protocol_version": 11,
	"generation": 1,
	"instance": {"name": "drift-suite-v11",
	             "authority_uuid": UUID,
	             "database": "work.sqlite3"},
	"teams": {
		"lang": {
			"display": "Language",
			"participants": {
				"ada":   {"display": "Ada", "roles": ["rsrch", "rev"],
				          "capabilities": ["config"]},
				"grace": {"display": "Grace", "roles": ["impl"]},
			},
			# W101: every declared role carries durable instructions.
			"roles": {"rsrch": {"display": "Research",
			                    "instructions": "Research and record."},
			          "impl":  {"display": "Implementation",
			                    "instructions": "Implement what is routed to you."},
			          "rev":   {"display": "Review",
			                    "instructions": "Review independently."}},
			"routes": {"intake": {"role": "rsrch", "handlers": ["ada"]},
			           "review": {"role": "rev", "handlers": ["ada"]}},
			"kinds": {"bug": {"display": "Bug intake", "route": "intake"},
			          "rev": {"display": "Review requests",
			                  "route": "review"}},
		},
		"web": {
			"display": "Web",
			"participants": {"wren": {"display": "Wren",
			                          "roles": ["dev"]}},
			"roles": {"dev": {"display": "Developer",
			                  "instructions": "Own this team's work."}},
			"routes": {"all": {"role": "dev", "handlers": ["wren"]}},
			"kinds": {"bug": {"display": "Bugs", "route": "all"}},
		},
	},
}


def _mutated(change) -> dict:
	document = copy.deepcopy(VALID)
	change(document)
	return document


def test_the_valid_document_loads_and_lists_participants():
	document = cfg.loads(json.dumps(VALID))
	assert document["generation"] == 1
	assert cfg.participants(document) == \
		["lang.ada", "lang.grace", "web.wren"]


def test_load_reads_a_file_and_names_it_in_refusals(tmp_path):
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(VALID))
	assert cfg.load(str(path))["instance"]["authority_uuid"] == UUID
	with pytest.raises(bw.WorkError, match="does not exist"):
		cfg.load(str(tmp_path / "absent.json"))
	bad = tmp_path / "bad.json"
	bad.write_text('{"config_version": 1,,}')
	with pytest.raises(bw.WorkError, match="bad.json.*not valid JSON"):
		cfg.load(str(bad))


def test_duplicate_keys_are_refused_at_parse():
	raw = json.dumps(VALID)[:-1] + ', "generation": 1}'
	with pytest.raises(bw.WorkError, match="duplicate object key"):
		cfg.loads(raw)
	# ...and a nested duplicate too — the hook runs at every level.
	nested = raw.replace('"display": "Language"',
	                     '"display": "Language", "display": "Language"', 1)
	with pytest.raises(bw.WorkError, match="duplicate object key 'display'"):
		cfg.loads(json.dumps(VALID).replace(
			'"display": "Language"',
			'"display": "L1", "display": "L2"', 1))


@pytest.mark.parametrize("change,fragment", [
	(lambda d: d.__setitem__("config_version", 2), "config_version"),
	(lambda d: d.__setitem__("protocol_version", 10), "speaks protocol 11"),
	(lambda d: d.__setitem__("generation", 0), "positive integer"),
	(lambda d: d.__setitem__("generation", True), "integer, not bool"),
	(lambda d: d.__setitem__("extra", 1), "unknown fields"),
	(lambda d: d.pop("instance"), "missing"),
	(lambda d: d["instance"].__setitem__("authority_uuid", "xyz"),
	 "32 lowercase hex"),
	(lambda d: d["instance"].__setitem__("database", "other.sqlite3"),
	 "fixed sibling"),
	(lambda d: d["instance"].__setitem__("surprise", 1), "unknown fields"),
	(lambda d: d["teams"]["lang"].__setitem__("outbox", {}), "unknown fields"),
	(lambda d: d["teams"]["lang"].__setitem__("display", "  "), "display"),
])
def test_document_level_refusals_name_the_field(change, fragment):
	with pytest.raises(bw.WorkError, match=fragment):
		cfg.loads(json.dumps(_mutated(change)))


@pytest.mark.parametrize("handle,fragment", [
	("implementer", "11 display cells"),
	("a.b", "reserves"),
	("", "non-empty"),
])
def test_the_handle_grammar_guards_every_identity_position(handle, fragment):
	for place in (
		lambda d, h: d["teams"].__setitem__(h, d["teams"].pop("web")),
		lambda d, h: d["teams"]["web"]["participants"].__setitem__(
			h, {"display": "X", "roles": ["dev"]}),
		lambda d, h: d["teams"]["web"]["roles"].__setitem__(
			h, {"display": "X"}),
		lambda d, h: d["teams"]["web"]["routes"].__setitem__(
			h, {"role": "dev", "handlers": ["wren"]}),
		lambda d, h: d["teams"]["web"]["kinds"].__setitem__(
			h, {"display": "X", "route": "all"}),
	):
		document = copy.deepcopy(VALID)
		place(document, handle)
		with pytest.raises(bw.WorkError, match=fragment):
			cfg.loads(json.dumps(document))


@pytest.mark.parametrize("change,fragment", [
	# membership and role assignment
	(lambda d: d["teams"]["lang"]["participants"]["ada"]["roles"].append(
		"ghost"), "does not declare"),
	(lambda d: d["teams"]["lang"]["participants"]["ada"].__setitem__(
		"capabilities", ["root"]), "capability 'root'"),
	(lambda d: d["teams"]["lang"].__setitem__("participants", {}),
	 "at least one participant"),
	# route coherence
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"role", "ghost"), "does not declare"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"handlers", []), "at least one handler"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"]["handlers"].append(
		"ghost"), "not a participant"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"handlers", ["grace"]), "does not hold role"),
	# kind mapping
	(lambda d: d["teams"]["lang"]["kinds"]["bug"].__setitem__(
		"route", "ghost"), "does not declare"),
	(lambda d: d["teams"]["lang"]["kinds"]["bug"].pop("route"), "missing"),
])
def test_reference_refusals_resolve_every_edge(change, fragment):
	with pytest.raises(bw.WorkError, match=fragment):
		cfg.loads(json.dumps(_mutated(change)))


def test_loading_is_pure(tmp_path):
	"""C1 performs no authority mutation — held the blunt way: loading
	creates no file and modifies none."""
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(VALID))
	before = sorted(os.listdir(tmp_path))
	stamp = path.stat().st_mtime_ns
	cfg.load(str(path))
	cfg.load(str(path))
	assert sorted(os.listdir(tmp_path)) == before
	assert path.stat().st_mtime_ns == stamp


# -- the reviewer's reproduced strictness gaps (C1 review, 2026-08-14) --------

@pytest.mark.parametrize("change,fragment", [
	# bool/float versions: bool is an int subclass and 1.0 == 1, so plain
	# equality admitted both.
	(lambda d: d.__setitem__("config_version", True), "integer, not bool"),
	(lambda d: d.__setitem__("config_version", 1.0), "integer, not float"),
	(lambda d: d.__setitem__("protocol_version", 11.0), "integer, not float"),
	(lambda d: d.__setitem__("protocol_version", True), "integer, not bool"),
	(lambda d: d.__setitem__("generation", 1.0), "integer, not float"),
	# duplicate lists: a repeated entry is a claim nothing distinguishes.
	(lambda d: d["teams"]["lang"]["participants"]["ada"].__setitem__(
		"roles", ["rev", "rev"]), "more than once"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"handlers", ["ada", "ada"]), "more than once"),
	(lambda d: d["teams"]["lang"]["participants"]["ada"].__setitem__(
		"capabilities", ["config", "config"]), "more than once"),
	# empty instance.
	(lambda d: d.__setitem__("teams", {}), "must not be empty"),
	# non-string references must refuse with the field named, never leak a
	# raw TypeError from a membership test.
	(lambda d: d["teams"]["lang"]["participants"]["ada"].__setitem__(
		"roles", [1]), "not a string"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"handlers", [None]), "not a string"),
	(lambda d: d["teams"]["lang"]["participants"]["ada"].__setitem__(
		"capabilities", 1), "must be a list"),
	(lambda d: d["teams"]["lang"]["routes"]["intake"].__setitem__(
		"role", 3), "does not declare"),
	(lambda d: d["teams"]["lang"]["kinds"]["bug"].__setitem__(
		"route", 3), "does not declare"),
])
def test_the_reproduced_gaps_are_closed(change, fragment):
	with pytest.raises(bw.WorkError, match=fragment):
		cfg.loads(json.dumps(_mutated(change)))


def test_no_input_raises_anything_but_workerror():
	"""The blanket form of "no raw TypeError leaks": a sweep of hostile
	shapes at every field may refuse only legibly."""
	hostile = [1, None, True, [], "x", {"a": 1}]
	def mutations():
		for value in hostile:
			yield lambda d, v=value: d.__setitem__("teams", v)
			yield lambda d, v=value: d["teams"].__setitem__("lang", v)
			for field in ("display", "participants", "roles", "routes",
			              "kinds"):
				yield lambda d, v=value, f=field: 					d["teams"]["lang"].__setitem__(f, v)
			yield lambda d, v=value: 				d["teams"]["lang"]["participants"].__setitem__("ada", v)
			yield lambda d, v=value: 				d["teams"]["lang"]["routes"].__setitem__("intake", v)
			yield lambda d, v=value: 				d["teams"]["lang"]["kinds"].__setitem__("bug", v)
			yield lambda d, v=value: d.__setitem__("instance", v)
	refused = 0
	for change in mutations():
		document = copy.deepcopy(VALID)
		change(document)
		raw = json.dumps(document)
		if json.dumps(VALID) == raw:
			continue
		try:
			cfg.loads(raw)
		except bw.WorkError:
			refused += 1
		# anything else propagates and fails the test as a raw leak
	assert refused > 40, f"the sweep barely swept ({refused})"
