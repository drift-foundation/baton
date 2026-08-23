"""W101: durable role instructions resolve through accepted configuration."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli, config, lifecycle, transitions    # noqa: E402
from test_config import VALID                                 # noqa: E402


def configured() -> dict:
	document = copy.deepcopy(VALID)
	document["teams"]["lang"]["roles"]["rsrch"]["instructions"] = \
		"Research first; distinguish observed facts from hypotheses."
	return document


def write_config(tmp_path, document) -> str:
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
	return str(path)


def test_role_instructions_are_strict_and_preserved_exactly():
	document = configured()
	loaded = config.loads(json.dumps(document))
	assert loaded["teams"]["lang"]["roles"]["rsrch"]["instructions"] == \
		"Research first; distinguish observed facts from hypotheses."
	for bad in ("", "   ", 7, ["research"]):
		broken = configured()
		broken["teams"]["lang"]["roles"]["rsrch"]["instructions"] = bad
		with pytest.raises(bw.WorkError,
		                   match="instructions.*non-empty string"):
			config.loads(json.dumps(broken))
	unknown = configured()
	unknown["teams"]["lang"]["roles"]["rsrch"]["prompt"] = "guess me"
	with pytest.raises(bw.WorkError, match="unknown fields.*prompt"):
		config.loads(json.dumps(unknown))


def test_selection_is_always_explicit_and_refuses_a_foreign_role():
	"""W101 supersedes its own inference rule.

	The role used to be optional when exactly one held role carried
	instructions. That made a deployment edit — giving a participant a
	second role — silently change the persona of every session launched
	for them. The role is now always named, even for a participant who
	holds exactly one, so participant, role and scope are auditable
	launch inputs rather than a value the launcher worked out."""
	document = config.loads(json.dumps(configured()))
	assert config.participant_instructions(document, "lang.ada", "rsrch") == {
		"participant": "lang.ada",
		"role": "rsrch",
		"instructions":
			"Research first; distinguish observed facts from hypotheses.",
		"configuration_generation": 1,
	}
	assert config.participant_instructions(
		document, "lang.ada", "rev")["instructions"] == "Review independently."
	with pytest.raises(bw.WorkError, match="does not hold role 'impl'"):
		config.participant_instructions(document, "lang.ada", "impl")
	for absent in (None, "", "   "):
		with pytest.raises(bw.WorkError, match="needs an explicit role="):
			config.participant_instructions(document, "lang.grace", absent)


def test_a_single_held_role_is_still_named_explicitly():
	"""The case the old rule optimized away. `lang.grace` holds exactly
	one role, so inference would have been unambiguous — and would have
	changed meaning the day grace gained a second."""
	document = config.loads(json.dumps(configured()))
	held = document["teams"]["lang"]["participants"]["grace"]["roles"]
	assert held == ["impl"], "the fixture no longer proves the single-role case"
	with pytest.raises(bw.WorkError, match="needs an explicit role="):
		config.participant_instructions(document, "lang.grace", None)
	assert config.participant_instructions(
		document, "lang.grace", "impl")["role"] == "impl"


def test_every_declared_role_must_carry_instructions():
	"""The universal contract: a deployment with any uninstructed role
	is incomplete and is refused at ACCEPTANCE, not at the launch that
	needed the text."""
	for role_handle in ("rsrch", "impl", "rev"):
		broken = configured()
		del broken["teams"]["lang"]["roles"][role_handle]["instructions"]
		with pytest.raises(bw.WorkError,
		                   match=f"role '{role_handle}' is missing"):
			config.loads(json.dumps(broken))
	spare = configured()
	spare["teams"]["lang"]["roles"]["spare"] = {"display": "Spare"}
	with pytest.raises(bw.WorkError, match="role 'spare' is missing"):
		config.loads(json.dumps(spare))


def test_the_contract_is_role_generic():
	"""'generic protocol validation must not encode those Baton-specific
	handles or paths'. Validation requires instructions on every
	declared role and never names one."""
	import inspect
	source = inspect.getsource(config)
	for baton_specific in ('"rview"', "'rview'", '"approv"', "'approv'",
	                       '"tuner"', "'tuner'", "AGENTS.md",
	                       "EFFECTIVE-BATON"):
		assert baton_specific not in source, \
			f"protocol validation hard-codes the Baton deployment's {baton_specific}"


def test_instructions_are_role_owned_not_copied_per_member():
	"""'Instructions remain role-owned and are not copied into member
	entries.' Correcting one role's text corrects every session started
	from it, and a member entry that tries to carry its own refuses."""
	document = configured()
	member = document["teams"]["lang"]["participants"]["ada"]
	member["instructions"] = "a private persona"
	with pytest.raises(bw.WorkError, match="unknown fields.*instructions"):
		config.loads(json.dumps(document))
	shared = config.loads(json.dumps(configured()))
	shared["teams"]["lang"]["participants"]["grace"]["roles"] = ["rsrch"]
	first = config.participant_instructions(shared, "lang.ada", "rsrch")
	second = config.participant_instructions(shared, "lang.grace", "rsrch")
	assert first["instructions"] == second["instructions"]


def test_the_cli_projects_only_accepted_instructions_and_reads_are_pure(
		tmp_path, capsys):
	path = write_config(tmp_path, configured())
	lifecycle.init_from_config(path, participant="lang.ada")
	database = tmp_path / "work.sqlite3"
	before = hashlib.sha256(database.read_bytes()).digest()
	assert cli.main(["--config", path, "--participant", "lang.ada",
	                 "instructions", "role=rsrch"]) == 0
	payload = json.loads(capsys.readouterr().out)
	assert payload["participant"] == "lang.ada"
	assert payload["result"]["role"] == "rsrch"
	assert payload["result"]["configuration_generation"] == 1
	assert hashlib.sha256(database.read_bytes()).digest() == before

	proposal = configured()
	proposal["generation"] = 2
	proposal["teams"]["lang"]["roles"]["rsrch"]["instructions"] = \
		"Changed but not accepted."
	write_config(tmp_path, proposal)
	assert cli.main(["--config", path, "--participant", "lang.ada",
	                 "instructions", "role=rsrch"]) == 1
	assert "edited but not accepted" in \
		json.loads(capsys.readouterr().err)["error"]


def test_regen_updates_instructions_without_changing_existing_work_or_topology(
		tmp_path):
	path = write_config(tmp_path, configured())
	lifecycle.init_from_config(path, participant="lang.ada")
	with lifecycle.open_bound(path) as store:
		work_id = transitions.create_work(
			store, team="lang", kind="bug", title="keep me",
			origin="self-initiated", classification="design-choice",
			author="ada", body="topology continuity")["work_id"]
	proposal = configured()
	proposal["generation"] = 2
	proposal["teams"]["lang"]["roles"]["rsrch"]["instructions"] = \
		"Generation two instructions."
	lifecycle.accept_config(write_config(tmp_path, proposal),
	                        actor="lang.ada")
	with lifecycle.open_bound(path) as store:
		assert store.conn.execute(
			"SELECT title FROM work WHERE id=?",
			(work_id,)).fetchone()["title"] == "keep me"
		assert [(row["team"], row["handle"], row["role"]) for row in
		        store.conn.execute("SELECT team, handle, role FROM routes "
		                           "WHERE removed=0 ORDER BY team, handle")] == [
			("lang", "intake", "rsrch"), ("lang", "review", "rev"),
			("web", "all", "dev")]
		resolved = config.participant_instructions(
			store.accepted_config, "lang.ada", "rsrch")
		assert resolved["instructions"] == "Generation two instructions."
		assert resolved["configuration_generation"] == 2


# -- the launch contract at the CLI boundary --------------------------------

def test_the_cli_refuses_an_instructions_read_without_a_role(tmp_path, capsys):
	"""`role=` is required grammar, so a launcher that lost its
	configured role fails closed at the boundary rather than starting a
	session with an unintended persona."""
	path = write_config(tmp_path, configured())
	lifecycle.init_from_config(path, participant="lang.ada")
	assert cli.main(["--config", path, "--participant", "lang.ada",
	                 "instructions"]) == 1
	assert "role" in json.loads(capsys.readouterr().err)["error"]


def test_the_cli_refuses_a_role_the_participant_does_not_hold(tmp_path,
                                                              capsys):
	path = write_config(tmp_path, configured())
	lifecycle.init_from_config(path, participant="lang.ada")
	assert cli.main(["--config", path, "--participant", "lang.ada",
	                 "instructions", "role=impl"]) == 1
	assert "does not hold role" in json.loads(capsys.readouterr().err)["error"]


# -- the shipped material ----------------------------------------------------

def _repo(*parts):
	return os.path.join(
		os.path.dirname(os.path.dirname(os.path.dirname(
			os.path.abspath(__file__)))), *parts)


def test_the_shipped_example_satisfies_the_universal_contract():
	"""`init` copies this file byte-for-byte, so an example that would
	be refused at acceptance ships a broken starting point."""
	with open(_repo("conf", "baton.example.json"), encoding="utf-8") as handle:
		document = config.loads(handle.read())
	for team_handle, team in document["teams"].items():
		assert team["roles"], f"{team_handle} declares no roles"
		for role_handle, role in team["roles"].items():
			assert role["instructions"].strip(), \
				f"{team_handle}.{role_handle} has empty instructions"


def test_the_shipped_example_states_the_required_reading():
	"""'the required bootstrap/read material' is half the contract, so
	the example demonstrates it rather than only describing authority."""
	with open(_repo("conf", "baton.example.json"), encoding="utf-8") as handle:
		document = config.loads(handle.read())
	roots = set(document.get("roots") or ())
	for team in document["teams"].values():
		for role_handle, role in team["roles"].items():
			text = role["instructions"]
			assert "read" in text.lower(), \
				f"{role_handle} names no required reading"
			assert any(f"{root}:" in text for root in roots), \
				f"{role_handle} names no configured-root reference"


def test_the_pinned_baton_role_texts_are_complete_and_acceptable():
	"""W101 step 8 records the exact `teams.baton.roles` block the next
	Baton generation must carry. Applying it is the approver's act, so
	this proves the material is valid and complete BEFORE that — a
	deployment step is a poor place to discover a malformed role."""
	import re
	path = _repo("work", "records", "2026", "08", "finding-v11-tuner-persona",
	             "ROLE-INSTRUCTIONS.md")
	with open(path, encoding="utf-8") as handle:
		found = re.search(r"```json\n(.*?)```", handle.read(), re.S)
	assert found, "the pinned role block is missing"
	roles = json.loads(found.group(1))
	assert sorted(roles) == ["approv", "impl", "rview", "tuner"], sorted(roles)
	for handle_name, role in roles.items():
		assert role["instructions"].strip()
		assert "baton:AGENTS.md" in role["instructions"], \
			f"{handle_name} does not name the repository policy read"
		assert "docs/EFFECTIVE-BATON.md" in role["instructions"], \
			f"{handle_name} does not name the operating guide"
		assert "dossier" in role["instructions"], \
			f"{handle_name} does not name the assigned dossier"
	document = copy.deepcopy(VALID)
	document["teams"]["lang"]["roles"] = roles
	document["teams"]["lang"]["participants"] = {
		"ada": {"display": "Ada", "roles": ["impl"],
		        "capabilities": ["config"]}}
	document["teams"]["lang"]["routes"] = {
		"intake": {"role": "impl", "handlers": ["ada"]}}
	document["teams"]["lang"]["kinds"] = {
		"bug": {"display": "Bug", "route": "intake"}}
	config.loads(json.dumps(document))


# -- the operator surfaces ---------------------------------------------------

def test_the_acp_guide_does_not_advertise_removed_role_inference():
	"""The explicit-role ruling reaches the guide an operator follows."""
	with open(_repo("tools", "acp-baton-bridge", "README.md"),
	          encoding="utf-8") as handle:
		acp_guide = handle.read()
	assert "baton.role` selects one role" in acp_guide
	assert "may be\n  omitted" not in acp_guide


def test_the_codex_usage_does_not_advertise_an_optional_role():
	"""A required launch operand must not be bracketed as optional."""
	with open(_repo("tools", "codex-event-bridge", "src", "main.mjs"),
	          encoding="utf-8") as handle:
		codex_main = handle.read()
	assert "--participant TEAM.MEMBER --role ROLE" in codex_main
	assert "--participant TEAM.MEMBER [--role ROLE]" not in codex_main


def test_no_shipped_operator_surface_advertises_role_inference():
	"""Sweep EVERY operator-facing surface, not the ones a review named.

	I fixed this twice: first the two setup guides while leaving the
	per-launcher README and `--help` stale, then those two while leaving
	the Codex bridge's own README and the topology document stale. Each
	time the fix was correct and the sweep was not, so the guard is a
	sweep rather than three more assertions.

	`ambiguous` is the tell. Under the explicit-role contract a
	participant's held roles cannot be ambiguous — the launcher names
	one — so any surface still offering to resolve ambiguity is
	describing the superseded model and will send an operator into a
	refusal from the very boundary these instructions exist to make
	reliable."""
	surfaces = [
		("docs", "BATON-SETUP.md"),
		("docs", "BATON-WORK.md"),
		("docs", "CODEX-APP-SERVER-EVENT-CONNECTIVITY.md"),
		("tools", "acp-baton-bridge", "README.md"),
		("tools", "codex-event-bridge", "README.md"),
		("tools", "codex-event-bridge", "src", "main.mjs"),
	]
	stale = []
	for parts in surfaces:
		with open(_repo(*parts), encoding="utf-8") as handle:
			text = handle.read()
		where = "/".join(parts)
		for line_number, line in enumerate(text.splitlines(), start=1):
			lowered = line.lower()
			if "role" not in lowered:
				continue
			for phrase in ("ambiguous", "may be omitted", "omitted only",
			               "[--role", "optional only when",
			               "exactly one instructed", "multiple instructed"):
				if phrase in lowered:
					stale.append(f"{where}:{line_number}: {line.strip()}")
	assert not stale, \
		"operator surfaces still describe inferred roles:\n" + "\n".join(stale)


def test_every_launch_surface_states_that_the_role_is_required():
	"""The positive half: each launcher's own guide must SAY so, not
	merely refuse at runtime. A refusal an operator cannot predict from
	the documentation is the failure this Work exists to remove."""
	with open(_repo("tools", "acp-baton-bridge", "README.md"),
	          encoding="utf-8") as handle:
		assert "is REQUIRED" in handle.read(), \
			"the ACP guide does not state that the role is required"
	with open(_repo("tools", "codex-event-bridge", "README.md"),
	          encoding="utf-8") as handle:
		text = handle.read()
	assert "`--role` is required" in text, \
		"the Codex guide does not state that --role is required"
	with open(_repo("tools", "codex-event-bridge", "src", "main.mjs"),
	          encoding="utf-8") as handle:
		assert "--participant TEAM.MEMBER --role ROLE" in handle.read()


# -- the required bootstrap policy -------------------------------------------

def test_required_repository_policy_does_not_bootstrap_retired_v10_coordination():
	"""Every pinned Baton role is required to read AGENTS.md before its
	first assignment. That makes this file part of the launch contract,
	not merely adjacent documentation: it must not inject retired v10
	identities or message-claim verbs into a protocol-11 session.

	The sweep covers the whole ACTIVE policy surface, not the strings a
	review happened to name. My first repair replaced the two identity
	strings and the readiness verbs and left `Current` and a role-shaped
	`review` phase standing two sections further down — the same
	fix-the-named-spot miss this Work has produced three times, so the
	guard is a sweep."""
	with open(_repo("AGENTS.md"), encoding="utf-8") as handle:
		policy = handle.read()
	# The renamed terms are COMPOSED rather than spelled out, for the
	# same reason W245's own scan composes its forbidden phrases: this
	# file is inside the source W245 scans, and a literal pairing of the
	# retired word with the noun it used to mean would be flagged by the
	# very guard that forbids teaching it.
	was_route = "".join(["Curr", "ent endpoint"])
	was_handler = "".join(["`Curr", "ent`"])
	retired = {
		"baton.reviewer": "the v10 reviewer identity",
		"baton.implementer": "the v10 implementer identity",
		"claim --message-id": "the v10 directed-claim verb",
		"`reply`": "the v10 answer verb",
		"head message": "the v10 mailbox readiness noun",
		"seen receipt": "the v10 receipt noun",
		was_route: "a pre-W245 eligibility noun",
		was_handler: "a pre-W245 claimant noun",
		"phase is `review`": "a role-shaped phase W38 removed",
		"`waiting`": "the pre-W78 name for the block phase",
	}
	stale = [f"{term} ({why})" for term, why in retired.items()
	         if term in policy]
	assert not stale, \
		"required AGENTS.md still bootstraps retired policy: " \
		+ ", ".join(stale)


def test_the_required_policy_states_the_v11_model():
	"""The positive half. Removing the retired words is not the same as
	describing the current model, and an agent reading this file before
	its first assignment needs the second."""
	with open(_repo("AGENTS.md"), encoding="utf-8") as handle:
		policy = handle.read()
	for required in ("baton.codex", "baton.claude", "baton.slaw",
	                 "Route, Handler and Next", "claim work=",
	                 "respond", "mark-seen"):
		assert required in policy, \
			f"the required policy never mentions {required!r}"


def test_the_required_policy_binds_one_operation_per_execution_request():
	"""W7830. A managed turn batched `detail` and `claim` into one
	execution request; the read ran, the mutation hit the ordinary sandbox
	and failed with a read-only database, and the Work stayed unclaimed.

	The deployment authorizes an EXACT canonical invocation, so a batch
	containing one is a different command. That rule has to be readable by
	every role before its first assignment, which is what this file is
	for — and it has to sit beside the mandatory claim, because the claim
	is the operation it binds hardest."""
	with open(_repo("AGENTS.md"), encoding="utf-8") as handle:
		policy = handle.read()
	for required in ("ONE standalone direct execution request",
	                 "never combined with `detail`",
	                 "shell control syntax",
	                 "never retry it inside a broader command"):
		assert required in policy, \
			f"the required policy never states {required!r}"
	# Adjacent to the claim it binds, not filed somewhere a reader of the
	# claim rules would never reach.
	claim_rules = policy.index("## The active-work claim")
	managed = policy.index("## Non-interactive managed turns")
	standalone = policy.index("ONE standalone direct execution request")
	assert claim_rules < standalone, \
		"the standalone-operation rule precedes the claim rules it binds"
	assert managed < standalone < policy.index(
		"A Codex context launched by readiness is non-interactive"), \
		"the standalone-operation rule is not the first managed-turn rule"
