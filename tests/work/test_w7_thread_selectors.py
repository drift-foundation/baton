"""W7 (finding-local-thread-selectors): visible local Thread selectors
are accepted.

The live projection-6.1 cutover refused `say thread=T2` from the very TUI
that displayed the born discussion as T2. One strict authority-local Thread
resolver now backs every Thread-valued operand — `say`, `thread`, `label`,
`unlabel`, and `mark-seen` — through the ONE central pre-dispatch pass, so
the canonical `<authority>-T<seq>` identity and the exact local `T<seq>`
spelling are interchangeable and fingerprint as one operation identity.
Malformed, missing, and foreign selectors fail closed by name without
mutation; JSON exposes the accepted local spelling; the TUI Threads pane
labels rows with it (never the Work-scoped label ordinal, which can
silently diverge).
"""

from __future__ import annotations

import contextlib
import io
import json as _json
import os
import pty as _pty
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield {"config": config, "store": store,
	       "database": result["database"],
	       "prefix": store.meta()["authority_uuid"][:8]}
	store.close()


def make(world, title="bound"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def run_cli(world, *argv):
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = cli.main(["--config", world["config"], "--participant",
		                 "lang.ada"] + list(argv))
	return code, out.getvalue(), err.getvalue()


def test_the_observed_refused_cutover_command_succeeds(world):
	"""The live incident, byte-shape faithful: the config acceptance
	holds seq 1, so the first Work is W2 with born discussion ...-T2 —
	`say thread=T2 ... on=W2` must succeed in its owning authority."""
	make(world, title="cutover target")
	code, out, err = run_cli(
		world, "say", "thread=T2",
		"body=v11 cutover test: acknowledge through v11",
		"request=lang.bug", "on=W2")
	assert code == 0, err
	posted = _json.loads(out)["result"]
	canonical = f"{world['prefix']}-T2"
	view = pj.thread(world["store"], canonical, viewer_team="lang",
	                 viewer_member="ada")
	assert any("acknowledge through v11" in message["body"]
	           for message in view["messages"]), posted


def test_all_five_thread_valued_verbs_share_the_resolver(world):
	"""say, thread, label, unlabel, mark-seen — each accepts the local
	spelling and lands on the SAME canonical thread."""
	make(world, title="carrier")          # W2, born T2
	make(world, title="other")            # W3, born T3
	canonical = f"{world['prefix']}-T2"

	code, out, _err = run_cli(world, "say", "thread=T2", "body=hello")
	assert code == 0
	code, out, _err = run_cli(world, "thread", "thread=T2")
	assert code == 0
	page = _json.loads(out)["result"]
	assert page["id"] == canonical
	assert page["local_id"] == "T2"
	assert any(message["body"] == "hello"
	           for message in page["messages"])

	code, _out, _err = run_cli(world, "label", "thread=T2", "work=W3")
	assert code == 0
	labelled = pj.thread(world["store"], canonical, viewer_team="lang",
	                     viewer_member="ada")
	assert [entry["work"] for entry in labelled["labels"]] == [
		f"{world['prefix']}-W2", f"{world['prefix']}-W3"]
	code, _out, _err = run_cli(world, "unlabel", "thread=T2",
	                           "work=W3")
	assert code == 0

	last = page["messages"][-1]["seq"]
	code, _out, _err = run_cli(world, "mark-seen", "thread=T2",
	                           f"up-to={last}")
	assert code == 0
	seen = pj.thread(world["store"], canonical, viewer_team="lang",
	                 viewer_member="ada")
	assert seen["new"] == 0, "mark-seen missed the resolved thread"


def test_both_spellings_are_one_operation_identity(world):
	"""Resolution precedes fingerprinting: an exact retry that swaps
	the canonical spelling for the local one REPLAYS instead of
	refusing or double-posting."""
	make(world, title="identity")
	canonical = f"{world['prefix']}-T2"
	code, out, err = run_cli(world, "say", "op-id=w7-parity",
	                         f"thread={canonical}", "body=once")
	assert code == 0, err
	first = _json.loads(out)["result"]
	code, out, err = run_cli(world, "say", "op-id=w7-parity",
	                         "thread=T2", "body=once")
	assert code == 0, err
	retry = _json.loads(out)["result"]
	assert retry["operation"]["state"] == "replayed", retry
	assert retry["seq"] == first["seq"]
	view = pj.thread(world["store"], canonical, viewer_team="lang",
	                 viewer_member="ada")
	assert sum(1 for message in view["messages"]
	           if message["body"] == "once") == 1


def test_malformed_missing_and_foreign_selectors_refuse_closed(world):
	make(world, title="guarded")
	store = world["store"]
	before = store.last_seq()
	for value, expected in [
			("T0", "not a Thread selector"),
			("T01", "not a Thread selector"),
			("t2", "not a Thread selector"),
			("T", "not a Thread selector"),
			("2", "not a Thread selector"),
			("T2x", "not a Thread selector"),
			("T-1", "not a Thread selector"),
			("W1", "not a Thread selector"),
			("deadbeef-T2", "names a different authority"),
			("T999", "no thread"),
	]:
		code, _out, err = run_cli(world, "say", f"thread={value}",
		                          "body=never lands")
		assert code == 1, f"{value!r} was accepted"
		assert expected in err, (value, err)
	assert store.last_seq() == before, \
		"a refused Thread selector consumed a sequence"


def test_thread_json_exposes_the_local_spelling(world):
	"""thread, threads, and work-threads each carry `local_id` beside
	the canonical id — and work-threads keeps its pagination ordinal
	untouched."""
	work = make(world, title="projected")
	tr.create_thread(world["store"], actor_team="lang", actor="ada",
	                 body="opener", labels=[work],
	                 subject="the follow-up questions")
	store = world["store"]
	listing = pj.threads_for(store, viewer_team="lang",
	                         viewer_member="ada")
	assert [(row["local_id"], row["id"]) for row in listing["rows"]] \
		== [(f"T{row['id'].rsplit('-T', 1)[1]}", row["id"])
		    for row in listing["rows"]]
	paged = pj.work_threads(store, work, viewer_team="lang",
	                        viewer_member="ada")
	assert [(row["ordinal"], row["local_id"]) for row in
	        paged["rows"]] == [(1, "T2"), (2, "T3")]


def _shuffle_labels(world):
	"""Force ordinal/identity divergence: W3 carries [T3 born, T4,
	T2 cross-labelled] in label order — the ordinal-based pane label
	would present T4's row as `T2` and T2's row as `T3`, each naming a
	DIFFERENT real thread of the same Work."""
	make(world, title="the record")                    # W2, born T2
	work = make(world, title="other record")           # W3, born T3
	tr.create_thread(world["store"], actor_team="lang", actor="ada",
	                 body="second opener", labels=[work],
	                 subject="the follow-up questions")  # T4
	tr.label_thread(world["store"], f"{world['prefix']}-T2", work,
	                actor_team="lang", actor="ada")
	return work


@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_the_pane_label_is_the_accepted_selector(world):
	"""The Threads pane renders the authority-local selector, and the
	command bar accepts exactly that spelling — even when label order
	diverges from creation order (where the old ordinal label would
	have pointed the operator at a DIFFERENT thread)."""
	_shuffle_labels(world)
	world["store"].close()
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada", [
			(b"j\r", 0.6),
			(b":say thread=T4 body=pane-spelling-proof\r", 0.9),
			(b"qy", 0.4),
		])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	pane = "\n".join(ptyharness.replay(steps[0]))
	assert "T4 the follow-up questions" in pane, pane[:1200]
	assert "T3 other record" in pane
	assert "T2 the record" in pane
	after = "\n".join(ptyharness.replay(steps[1]))
	assert "no thread" not in after.lower(), after[:1200]
	store = bw.Authority(world["database"])
	try:
		view = pj.thread(store, f"{world['prefix']}-T4",
		                 viewer_team="lang", viewer_member="ada")
		assert any(message["body"] == "pane-spelling-proof"
		           for message in view["messages"]), \
			"the pane spelling did not land on its displayed thread"
	finally:
		store.close()


@pytest.mark.serial
@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_packaged_console_accepts_the_displayed_selector(tmp_path):
	"""The observed cutover path through the DEPLOYED artifact: the
	packaged console displays a Thread selector and its own `:` bar
	accepts that exact spelling."""
	repo = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	deployed = subprocess.run(
		[sys.executable, os.path.join(repo, "tools", "deploy_work.py"),
		 os.path.join(str(tmp_path), "release")],
		capture_output=True, text=True, timeout=300)
	assert deployed.returncode == 0, deployed.stderr
	executable = _json.loads(deployed.stdout)["executable"]
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}

	home = os.path.join(str(tmp_path), "home")
	os.mkdir(home)
	assert subprocess.run([executable, "init", f"directory={home}"],
	                      capture_output=True, text=True, env=env,
	                      timeout=120).returncode == 0
	config = os.path.join(home, "baton.json")
	with open(config, encoding="utf-8") as handle:
		document = _json.load(handle)
	document["teams"] = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]},
		          "kinds": ["bug"]}})["teams"]
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)

	def run(*argv):
		return subprocess.run(
			[executable, "--config", config, "--participant",
			 "lang.ada"] + list(argv),
			capture_output=True, text=True, env=env, timeout=120)

	assert run("activate", f"directory={home}").returncode == 0
	made = run("create", "team=lang", "kind=bug",
	           "title=cutover target", "origin=external-report",
	           "classification=suspected-defect", "body=born")
	assert made.returncode == 0, made.stderr

	text, status, steps = ptyharness.drive(
		config, "lang.ada", [
			(b"\r", 0.6),
			(b":say thread=T2 body=packaged-cutover-proof\r", 0.9),
			(b"qy", 0.4),
		], command=[executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, \
		text[-400:]
	pane = "\n".join(ptyharness.replay(steps[0]))
	assert "T2 cutover target" in pane, pane[:1200]
	page = run("thread", "thread=T2")
	assert page.returncode == 0, page.stderr
	result = _json.loads(page.stdout)["result"]
	assert result["local_id"] == "T2"
	assert any(message["body"] == "packaged-cutover-proof"
	           for message in result["messages"]), \
		"the packaged pane spelling did not reach its thread"
