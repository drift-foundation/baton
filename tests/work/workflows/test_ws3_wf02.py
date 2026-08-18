"""WS3-WF-02 — N-consumer convergence through atomic acceptance
(WS3-DESIGN.md D4).

Three independent reports converge on one provider Work through three
atomic accepts: each edge carries its own provenance, each consumer's
thread carries its own rationale, DEP tracks the live load, a
duplicate acceptance attempt refuses without a byte, and the terminal
close fans out through every provenance edge at once.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_final_invariants,                # noqa: E402
                      assert_refusal_changes_nothing, document, team)

MEMBERS = {"push": "sl", "web": "wren", "mdb": "mo"}


def _teams() -> dict:
	spec = {}
	for name, member in MEMBERS.items():
		spec[name] = team(
			name.title(),
			{member: {"display": member.title(), "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": [member]}},
			{"bug": {"display": "Bug", "route": "main"}})
	spec["drift"] = team(
		"Drift",
		{"ada": {"display": "Ada", "roles": ["dev"],
		         "capabilities": ["config"]}},
		{"dev": {"display": "Developer"}},
		{"main": {"role": "dev", "handlers": ["ada"]}},
		{"bug": {"display": "Bug", "route": "main"},
		 "rsrch": {"display": "Research", "route": "main"}})
	return spec


def test_ws3_wf02_convergence_through_acceptance(flow):
	flow.init(document(_teams()))

	# Three independent reports, each asking @drift.bug and waiting on
	# exactly its own question.
	consumers, questions = {}, {}
	for name, member in MEMBERS.items():
		work = flow.ok("create", f"team={name}", "kind=bug",
		               f"title={name} report",
		               "origin=external-report", "classification=suspected-defect", "body=local report",
		               viewer=f"{name}.{member}")["work_id"]
		# W159: each consumer claims, then asks in ONE act that
		# suspends it on exactly its own question.
		flow.ok("claim", f"work={work}", viewer=f"{name}.{member}")
		asked = flow.post(work, "body=drift: yours?",
		                "request=drift.bug",
		                viewer=f"{name}.{member}")
		suspended = flow.ok("detail", f"work={work}",
		                    viewer=f"{name}.{member}")
		assert suspended["phase"] == "block"
		assert suspended["gate"]["obligation"]["seq"] == asked["seq"]
		assert suspended["handler"] is None
		consumers[name], questions[name] = work, asked["seq"]

	# The first acceptance creates DRIFT-1; the other two converge into it.
	first = flow.ok("accept", f"obligation={questions["push"]}",
	                "body=ours; tracking as parser recovery",
	                "create=true", "kind=rsrch",
	                "classification=suspected-defect",
	                "title=parser recovery", viewer="drift.ada")
	drift1 = first["provider"]
	for name in ("web", "mdb"):
		flow.ok("accept", f"obligation={questions[name]}",
		        f"body=same parser regression as {drift1}",
		        f"into={drift1}", viewer="drift.ada")

	# Live DEP=3; every edge explains itself through its own obligation.
	provider = flow.ok("detail", f"work={drift1}", viewer="drift.ada")
	assert provider["open_dependents"] == 3
	assert {entry["via_obligation"] for entry in
	        provider["links"]["blocks"]} == set(questions.values())
	for name, member in MEMBERS.items():
		checkpoint = flow.ok("detail", f"work={consumers[name]}",
		                     viewer=f"{name}.{member}")
		# W38 R3: each acceptance gated its consumer on the shared
		# provider, so the obligation wait retargets onto that gate
		# instead of advertising the consumer as runnable.
		assert checkpoint["phase"] == "block", f"{name} slept on"
		assert checkpoint["gate"]["kind"] == "work"
		assert checkpoint["ready"] is False
		assert checkpoint["links"]["blocked_by"][0]["via_obligation"] == \
			questions[name]
		assert flow.ok("home", viewer=f"{name}.{member}")["rows"][0][
			"id"] == consumers[name], "default views lost noise scoping"

	# A duplicate acceptance attempt refuses without a byte.
	error = assert_refusal_changes_nothing(
		flow, "drift.ada", "accept", f"obligation={questions["push"]}",
		"body=twice", f"into={drift1}")
	assert "already accepted" in error

	# The terminal close fans out through all three provenance edges.
	flow.ok("close", f"work={drift1}", "rationale=fixed and verified",
	        "outcome=satisfying", viewer="drift.ada")
	for name, member in MEMBERS.items():
		resumed = flow.ok("detail", f"work={consumers[name]}",
		                  viewer=f"{name}.{member}")
		assert resumed["ready"] is True
		assert resumed["links"]["blocked_by"][0]["outcome"] == "satisfying"
		flow.ok("close", f"work={consumers[name]}", "rationale=verified",
		        "outcome=satisfying", viewer=f"{name}.{member}")
	assert flow.ok("detail", f"work={drift1}", viewer="drift.ada")["open_dependents"] == 0
	assert_final_invariants(flow, "drift.ada",
	                        [drift1, *consumers.values()])
