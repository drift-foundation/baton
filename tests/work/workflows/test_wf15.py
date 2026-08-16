"""WF-15 — onboarding a coordination home from an empty directory
(WORKFLOW-TESTS.md, WS-6 Slice B).

`init DIR` writes the editable scaffold — valid strict JSON plus
separate Markdown instructions, no database — and is deliberately
one-shot with manual recovery; `activate` remains the ONE authoritative
validation and creation, refusing whole and leaving nothing until the
edited document passes; a protected activation replays exactly; a raced
activation admits one winner; a partially-populated directory refuses
by name rather than being adopted.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      standard_teams)


def _document(home: str) -> dict:
	with open(os.path.join(home, "baton.json"), encoding="utf-8") as \
			handle:
		return json.load(handle)


def _write(home: str, document: dict) -> None:
	with open(os.path.join(home, "baton.json"), "w",
	          encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
		handle.write("\n")


def test_wf15_onboarding_from_an_empty_directory(flow, tmp_path):
	home = flow.directory

	# 1. `init` scaffolds the editable home: strict JSON that parses,
	# instructions that name the next act, and NO database.
	scaffold = flow.ok("init", f"directory={home}")
	assert sorted(scaffold["created"]) == \
		["BATON-SETUP.md", "baton.json"]
	with open(os.path.join(home, "BATON-SETUP.md"),
	          encoding="utf-8") as handle:
		assert "baton --participant team.member activate " \
			"directory=." in handle.read()
	proposed = _document(home)
	assert proposed["generation"] == 1 and proposed["teams"] == {}
	uuid = proposed["instance"]["authority_uuid"]
	database = os.path.join(home, "work.sqlite3")
	assert not os.path.exists(database)

	# 2. init is ONE-SHOT: a re-run refuses whole, naming the managed
	# blockers and demanding manual inspection — never adopt, resume,
	# overwrite, or delete.
	error = flow.refuse("init", f"directory={home}")
	assert "already contains" in error and "manual cleanup" in error

	# 3. Activating the PRISTINE scaffold refuses with the real
	# semantic message and leaves no database to clean up.
	error = flow.refuse("activate", f"directory={home}", viewer="lang.ada")
	assert "teams must not be empty" in error
	assert not os.path.exists(database)

	# 4. A half-edited document refuses whole through the same strict
	# gate: a stray field is named, and still nothing exists.
	broken = _document(home)
	broken["teams"] = standard_teams()
	broken["surprise"] = "left over from an editor template"
	_write(home, broken)
	error = flow.refuse("activate", f"directory={home}", viewer="lang.ada")
	assert "unknown fields" in error and "surprise" in error
	assert not os.path.exists(database)

	# 5. The completed edit activates under an operation identity; the
	# scaffold's authority uuid is the one the instance keeps; an exact
	# retry REPLAYS the one committed activation.
	del broken["surprise"]
	_write(home, broken)
	activated = flow.ok("activate", "op-id=onboard-1", f"directory={home}",
	                    viewer="lang.ada")
	assert activated["generation"] == 1
	assert activated["authority_uuid"] == uuid
	assert os.path.exists(database)
	replay = flow.ok("activate", "op-id=onboard-1", f"directory={home}",
	                 viewer="lang.ada")
	assert replay["operation"]["state"] == "replayed"

	# 6. The activated instance is immediately real for its members:
	# create, say, thread, home — two different participants, all
	# through the public surface.
	work = flow.ok("create", "team=push", "kind=bug",
	               "title=first report",
	               "origin=external-report", "classification=suspected-defect", "body=onboarded",
	               viewer="push.sl")["work_id"]
	flow.post(work, "body=triaging now", viewer="push.sl")
	thread = flow.ok("thread", f"thread={flow.born(work, 'push.sl')}",
	                 viewer="push.sl")
	assert [entry["body"] for entry in thread["messages"]][-1] == \
		"triaging now"
	assert flow.ok("home", viewer="lang.ada") is not None

	# 7. A RACED activation of a second fresh home admits exactly one
	# winner; the loser refuses structurally and the home holds one
	# authority.
	second = os.path.join(str(tmp_path), "second")
	os.mkdir(second)
	flow.ok("init", f"directory={second}")
	fresh = _document(second)
	fresh["teams"] = standard_teams()
	_write(second, fresh)
	procs = [flow.spawn("activate", f"op-id=race-{index}", f"directory={second}",
	                    viewer="lang.ada") for index in range(2)]
	finished = [flow.finish(proc) for proc in procs]
	winners = [out for code, out, _err in finished if code == 0]
	losers = [err for code, _out, err in finished if code != 0]
	assert len(winners) == 1 and len(losers) == 1, finished
	assert json.loads(losers[0])["error"]
	assert os.path.exists(os.path.join(second, "work.sqlite3"))

	# 8. A partially-populated directory is never adopted: one stray
	# managed file blocks init BY NAME; a missing directory refuses
	# rather than being invented.
	stray = os.path.join(str(tmp_path), "stray")
	os.mkdir(stray)
	with open(os.path.join(stray, "baton.json"), "w") as handle:
		handle.write("{}")
	error = flow.refuse("init", f"directory={stray}")
	assert "baton.json" in error
	error = flow.refuse("init", f"directory={os.path.join(str(tmp_path), 'absent')}")
	assert "not an existing directory" in error

	assert_dense_audit(flow, "lang.ada")
