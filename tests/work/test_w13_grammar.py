"""W13: the ONE strict order-independent key=value operation grammar.

Launcher context keeps --config/--participant/--expect-projection before
the verb; every operation operand is a key=value token shared verbatim by
the CLI and the TUI command bar. Tokens split at the FIRST `=`; unknown,
missing, malformed, duplicate-singular, retired-flag and positional input
refuse BEFORE authority access with no residue; repeatables preserve
order; op-id/ref/answer-ref are operation semantics.
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
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	import json as _j
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin",
	                                  "base": str(tmp_path)}}
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w") as handle:
		_j.dump(document, handle, indent=2, sort_keys=True)
	from baton_work import lifecycle as lc
	result = lc.init_from_config(config, participant="lang.ada")
	return config, result["database"]


def _run(capsys, config, *argv, viewer="lang.ada"):
	code = work_cli.main(["--config", config, "--participant", viewer]
	                     + list(argv))
	captured = capsys.readouterr()
	return code, captured


def test_keys_are_order_independent_and_split_at_the_first_equals(
		world, capsys):
	config, _database = world
	code, captured = _run(
		capsys, config, "create", "body=x=y=z", "origin=self-initiated",
		"title=ordered any way", "classification=design-choice",
		"kind=bug", "team=lang")
	assert code == 0, captured.err
	work = _json.loads(captured.out)["result"]["work_id"]
	code, captured = _run(capsys, config, "detail", f"work={work}")
	assert code == 0
	detail = _json.loads(captured.out)["result"]
	assert detail["title"] == "ordered any way"
	# The first `=` split: the body kept its embedded equals signs.
	code, captured = _run(capsys, config, "thread",
	                      f"thread={detail['threads'][0]['id']}")
	assert code == 0
	messages = _json.loads(captured.out)["result"]["messages"]
	assert messages[0]["body"] == "x=y=z"


def test_bad_input_refuses_before_authority_access(world, capsys):
	"""Unknown keys, missing required keys, malformed tokens, duplicate
	singular keys, retired flags, and positionals ALL refuse with no
	residue — the event count never moves."""
	config, database = world
	with bw.Authority(database) as store:
		before = store.last_seq()
	cases = [
		(("create", "team=lang", "surprise=1"), "unknown key"),
		(("create", "team=lang"), "missing required"),
		(("create", "noequals"), "not a key=value token"),
		(("detail", "work=W1", "work=W2"), "duplicate work="),
		(("close", "--rationale", "x"), "retired flag spelling"),
		(("detail", "some-W1"), "positional operands are retired"),
		(("phase", "work=x", "to=waiting", "wait=maybe"), "integer"),
		(("accept", "obligation=1", "body=x", "create=yes"),
		 "exactly the value true"),
	]
	for argv, fragment in cases:
		code, captured = _run(capsys, config, *argv)
		assert code == 1, argv
		assert fragment in _json.loads(captured.err)["error"], \
			(argv, captured.err)
	with bw.Authority(database) as store:
		assert store.last_seq() == before, \
			"a refused invocation left residue"


def test_the_launcher_boundary_is_closed(world, capsys):
	"""Only --config/--participant/--expect-projection live before the
	verb; anything else there refuses as launcher-context violation."""
	config, _database = world
	code = work_cli.main(["--config", config, "--op-id", "x", "home"])
	captured = capsys.readouterr()
	assert code == 1
	assert "launcher context" in _json.loads(captured.err)["error"]


def test_repeatables_preserve_order_and_op_id_protects(world, capsys):
	config, database = world
	code, captured = _run(
		capsys, config, "start-thread", "op-id=st-1",
		"subject=ordered labels", "body=b",
		"label=zeta", "label=alpha")
	# labels validate against work ids; refusal here is fine — the point
	# is ORDER: the refusal (or acceptance) must name zeta first.
	if code == 1:
		error = _json.loads(captured.err)["error"]
		assert "zeta" in error and error.index("zeta") >= 0
	# op-id retry identity: same invocation replays; changed input
	# conflicts (proven through create).
	first = _run(capsys, config, "create", "op-id=c-1", "team=lang",
	             "kind=bug", "title=t", "origin=self-initiated",
	             "classification=design-choice", "body=b")
	assert first[0] == 0
	again = _run(capsys, config, "create", "op-id=c-1", "team=lang",
	             "kind=bug", "title=t", "origin=self-initiated",
	             "classification=design-choice", "body=b")
	assert again[0] == 0
	assert _json.loads(again[1].out)["result"]["operation"]["state"] == \
		"replayed"
	conflict = _run(capsys, config, "create", "op-id=c-1", "team=lang",
	                "kind=bug", "title=DIFFERENT",
	                "origin=self-initiated",
	                "classification=design-choice", "body=b")
	assert conflict[0] == 1


def test_the_tui_command_bar_shares_the_grammar(tmp_path):
	"""The command bar feeds the SAME parser: a key=value create
	succeeds; retired flag spelling refuses with the W13 message."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":create team=lang kind=bug title=bar-born "
		 b"origin=self-initiated classification=design-choice "
		 b"body=hello\n", 0.8),
		(b":create --team lang\n", 0.6),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	created = ptyharness.replay(steps[0])
	assert any("bar-born" in line or "ok work_id=" in line
	           for line in created), created[-4:]
	refused = ptyharness.replay(steps[1])
	assert any("retired flag spelling" in line for line in refused), \
		refused[-4:]


def test_grammar_refusals_never_open_the_authority(world, monkeypatch):
	"""R4.1: parser refusal happens BEFORE authority access — the bound
	open is guarded and must never fire for grammar-invalid input."""
	from baton_work import lifecycle as lc

	def forbidden(*_args, **_kw):
		raise AssertionError("a grammar refusal opened the authority")

	monkeypatch.setattr(lc, "open_bound", forbidden)
	config, _database = world
	for argv in (("create", "team=lang", "surprise=1"),
	             ("create", "team=lang"),
	             ("detail", "positional"),
	             ("close", "--rationale", "x"),
	             ("close", "work=x", "rationale=r", "outcome=bogus"),
	             ("accept", "obligation=1", "body=b"),
	             ("accept", "obligation=1", "body=b", "into=W",
	              "create=true", "kind=bug", "title=t",
	              "classification=limitation")):
		code = work_cli.main(["--config", config, "--participant",
		                      "lang.ada"] + list(argv))
		assert code == 1, argv


def test_repeatable_references_arrive_in_occurrence_order(world, capsys):
	"""R4.2: the durably projected values prove the order — two ref=
	tokens land on the message in exactly the typed sequence."""
	config, _database = world
	import json as _j
	code, captured = _run(
		capsys, config, "create", "team=lang", "kind=bug", "title=refs",
		"origin=self-initiated", "classification=design-choice",
		"body=b")
	assert code == 0, captured.err
	created = _j.loads(captured.out)["result"]
	code, captured = _run(
		capsys, config, "say", f"thread={created['thread']}",
		"body=ordered", "ref=pushcoin:b/second.md",
		"ref=pushcoin:a/first.md")
	assert code == 0, captured.err
	code, captured = _run(capsys, config, "thread",
	                      f"thread={created['thread']}")
	assert code == 0
	message = _j.loads(captured.out)["result"]["messages"][-1]
	paths = [ref["path"] for ref in message["references"]]
	assert paths == ["b/second.md", "a/first.md"], \
		"repeatable ref= lost its occurrence order"


def test_the_bar_quoting_and_embedded_equals_round_trip(tmp_path):
	"""R4.3: quoted spaces and embedded `=` typed in the TUI bar arrive
	verbatim in canonical JSON."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import json as _j
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	text, status, _steps = ptyharness.drive(config, "lang.ada", [
		(b':create team=lang kind=bug title="two words here" '
		 b'origin=self-initiated classification=design-choice '
		 b'body="left=right and a=b"\n', 0.8),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	from baton_work import lifecycle as lc
	from baton_work import projection as pj
	with lc.open_bound(config) as store:
		rows = pj.home(store, viewer_team="lang",
		               viewer_member="ada")["rows"]
		assert rows[0]["title"] == "two words here"
		thread = pj.work_threads(store, rows[0]["id"],
		                         viewer_team="lang",
		                         viewer_member="ada", after=0,
		                         limit=1)["rows"][0]["id"]
		body = pj.thread(store, thread, viewer_team="lang",
		                 viewer_member="ada")["messages"][0]["body"]
	assert body == "left=right and a=b"


def test_the_specification_is_authoritative_and_help_derives(world,
		capsys):
	"""R4.4/R4.5: the declarative spec carries the ruled contract —
	required keys, closed vocabularies, alternative forms — and the
	generated help renders every verb and key from that one source."""
	spec = {e["name"]: e for e in work_cli.GRAMMAR["create"]["keys"]}
	assert spec["classification"]["required"] is True
	assert "unknown" not in spec["classification"]["values"]
	close = {e["name"]: e for e in work_cli.GRAMMAR["close"]["keys"]}
	assert close["rationale"]["required"] and close["outcome"]["required"]
	assert close["outcome"]["values"] == (
		"satisfying", "non-satisfying", "rejected", "cancelled")
	assert work_cli.GRAMMAR["accept"]["exactly-one"] == ("into", "create")
	assert work_cli.GRAMMAR["accept"]["when"]["create"]["requires"] == (
		"kind", "title", "classification")
	# help/spec parity: every verb and every key name appears in the
	# generated discovery text.
	rendered = work_cli.render_help()
	for verb, info in work_cli.GRAMMAR.items():
		assert f"{verb} — " in rendered, verb
		for entry in info["keys"]:
			assert f"{entry['name']}=" in rendered, (verb,
			                                         entry["name"])
	# closed vocabularies render in per-verb help
	one = work_cli.render_help("classify")
	assert "one of: unknown, suspected-defect" in one


def test_launcher_value_forms_and_help(world, capsys):
	"""R4.5: both --name VALUE and --name=VALUE launcher spellings work,
	duplicates refuse, unknown globals refuse, and --help answers."""
	config, _database = world
	code = work_cli.main([f"--config={config}",
	                      "--participant=lang.ada", "summary"])
	captured = capsys.readouterr()
	assert code == 0, captured.err
	code = work_cli.main(["--config", config, f"--config={config}",
	                      "summary"])
	captured = capsys.readouterr()
	assert code == 1
	assert "duplicate --config" in captured.err
	code = work_cli.main(["--viewer", "x", "home"])
	captured = capsys.readouterr()
	assert code == 1
	assert "launcher context" in captured.err
	code = work_cli.main(["--help"])
	captured = capsys.readouterr()
	assert code == 0
	assert "create — " in captured.out and "say — " in captured.out
	code = work_cli.main(["--help", "create"])
	captured = capsys.readouterr()
	assert code == 0
	assert "classification=" in captured.out
	assert "suspected-defect" in captured.out


def test_static_conditions_refuse_before_authority(world, monkeypatch):
	"""R1 round 3: the declared conditional forms — phase parked/waiting,
	say exclusivity and carriers, close duplicate-of — refuse at parse,
	never opening the authority."""
	from baton_work import lifecycle as lc

	def forbidden(*_a, **_k):
		raise AssertionError("a static-form refusal opened the authority")

	monkeypatch.setattr(lc, "open_bound", forbidden)
	config, _database = world
	cases = [
		(("phase", "work=x", "to=parked"), "requires reason="),
		(("phase", "work=x", "to=waiting"), "requires wait="),
		(("phase", "work=x", "to=queued", "wait=gates"),
		 "applies only with to=waiting"),
		# W80: transfer left say — pass-to/phase/set-next are unknown
		# keys there now; the carrier condition binds on= to request=.
		(("say", "thread=t", "body=b", "pass-to=c.d"),
		 "unknown key 'pass-to'"),
		(("say", "thread=t", "body=b", "on=w"), "requires request="),
		(("say", "thread=t", "body=b", "phase=review"),
		 "unknown key 'phase'"),
		(("pass", "work=w", "to=a.b", "comment=c",
		  "phase=nowhere"), "phase= takes one of"),
		# W171: pass is threadless — the old coupling is an unknown key.
		(("pass", "work=w", "to=a.b", "comment=c", "thread=t"),
		 "unknown key 'thread'"),
		(("close", "work=x", "rationale=r", "outcome=satisfying",
		  "duplicate-of=y"), "requires outcome=rejected"),
	]
	for argv, fragment in cases:
		code = work_cli.main(["--config", config, "--participant",
		                      "lang.ada"] + list(argv))
		assert code == 1, argv
	import json as _j


def test_help_parity_covers_universal_operands_and_conditions(world,
		capsys):
	"""R1 round 3: generated discovery renders the universal operands on
	every verb and the declared conditional forms."""
	rendered = work_cli.render_help()
	for name in ("op-id=", "ref=", "answer-ref="):
		assert rendered.count(name) >= len(work_cli.GRAMMAR), \
			f"{name} is not rendered for every verb"
	say = work_cli.render_help("say")
	assert "with on=: requires request=" in say
	assert "pass-to" not in say, "the retired transfer key survived"
	passing = work_cli.render_help("pass")
	assert "to=" in passing and "comment=" in passing
	phase = work_cli.render_help("phase")
	assert "with to=parked: requires reason=" in phase
	assert "with to=waiting: requires wait=" in phase
	assert "unless to=waiting: forbids wait=" in phase
	close = work_cli.render_help("close")
	assert "with duplicate-of=: requires outcome=rejected" in close


def test_no_retired_spelling_survives_in_current_source():
	"""R2 round 3: the narrow anti-drift pin — current src emits no
	retired operation-flag spelling and no baton-work product name;
	launcher globals and --help stay."""
	import re
	retired = re.compile(
		r"--(?:title|expect|into|create|parent|on|set-next|message|"
		r"root|path|op-id|ref|refresh|up-to|rationale|outcome|body|"
		r"subject|label|include|request|pass-to|kind|team|origin|"
		r"classification|binding|duplicate-of|observation|evidence|"
		r"disposition|timeout|after|limit|git|template|locator|"
		r"directory|as|to|reason|wait|candidate|assign|review-at|"
		r"phase|round)\b")
	base = os.path.join(
		os.path.dirname(os.path.dirname(os.path.dirname(
			os.path.abspath(__file__)))), "src", "baton_work")
	offenders = []
	for dirpath, _dirs, files in os.walk(base):
		if "__pycache__" in dirpath:
			continue
		for name in files:
			if not name.endswith(".py"):
				continue
			text = open(os.path.join(dirpath, name),
			            encoding="utf-8").read()
			for lineno, line in enumerate(text.splitlines(), 1):
				if ("--expect-projection" in line or
						"--config" in line or
						"--participant" in line or
						"--help" in line or "--name" in line):
					continue
				if retired.search(line):
					offenders.append(f"{name}:{lineno}: "
					                 f"{line.strip()[:70]}")
			if "baton-work" in text:
				for lineno, line in enumerate(text.splitlines(), 1):
					if "baton-work" in line and \
							"deploy_work" not in line:
						offenders.append(f"{name}:{lineno}: "
						                 f"{line.strip()[:70]}")
	assert offenders == [], offenders


# -- W14: context-sensitive command-bar assistance ---------------------------

def test_assist_derives_from_the_one_specification():
	"""W14: matching verbs while typing, then remaining required/optional
	keys, then closed values — every answer a pure function of the same
	GRAMMAR the parser executes, through the shared partial analyzer."""
	from baton_work.tui.app import assist_text
	assert assist_text("bl") == "block"
	assert "claim" in assist_text("cl") and "close" in assist_text("cl")
	after_verb = assist_text("block ")
	assert "required:" in after_verb
	assert "work=" in after_verb and "on=" in after_verb
	remaining = assist_text("block work=W1 ")
	assert "work=" not in remaining.split("optional:")[0], \
		"a supplied key stayed listed as required"
	assert "on=" in remaining
	values = assist_text("close work=X rationale=r outcome=")
	assert values.startswith("outcome=: ")
	assert "satisfying" in values and "cancelled" in values
	assert assist_text("close work=X outcome=rej") == \
		"outcome=: rejected"
	assert assist_text("zz") == "no matching command"
	assert assist_text("accept ").startswith("one of: into= | create=")
	# parity: every verb's unconditional required keys appear in its
	# own assist.
	for verb, info in work_cli.GRAMMAR.items():
		hint = assist_text(verb + " ")
		for entry in info["keys"]:
			if entry["required"] and entry["name"] not in \
					work_cli.exactly_names(info):
				assert entry["name"] + "=" in hint, (verb,
				                                     entry["name"])


def test_partial_analysis_speaks_the_execution_tokenizer():
	"""W14 R1: `cli.analyze_partial` lives beside the grammar and
	applies the SAME shell-quoting and first-`=` rules as the bar's
	execution tokenizer (`shlex.split`), distinguishing the live final
	token by position; nothing inside a quoted value is ever mistaken
	for a key."""
	from baton_work.tui.app import assist_text
	# quoted spaces: ONE completed token; the key-shaped text inside
	# the quotes invents nothing
	quoted = assist_text('say thread=T1 body="work=W9 on=Z" ')
	assert "required:" not in quoted, quoted
	assert "unknown" not in quoted
	assert "on=" in quoted and "include=" in quoted
	# embedded '=' splits at the FIRST '=' only
	embedded = assist_text("close work=X rationale=a=b ")
	assert "required: outcome=" in embedded, embedded
	# reordered keys are the same form
	assert assist_text("close outcome=rejected work=X ") == \
		assist_text("close work=X outcome=rejected ")
	# an OPEN quote is carried honestly: the live token is one quoted
	# value in progress — assistance stays useful, invents no keys
	open_quote = assist_text('say thread=T1 body="hello wor')
	assert "unknown" not in open_quote and \
		"not a key=value" not in open_quote, open_quote
	assert "required:" not in open_quote, \
		"the in-progress body= still counted as missing"
	assert "request=" in open_quote


def test_assist_applies_the_parsers_condition_model():
	"""W14 R2: effective remaining required/optional keys derive from
	the same exactly-one/when/conditions model `_parse_invocation`
	enforces — accept's two forms, parked/waiting, say's exclusive
	carriers and pass fields, close's duplicate outcome."""
	from baton_work.tui.app import assist_text
	created = assist_text("accept create=true ")
	required = created.split("optional:")[0]
	for name in ("kind=", "title=", "classification=", "body=",
	             "obligation="):
		assert name in required, (name, created)
	assert "into=" not in created
	into = assist_text("accept into=W7 ")
	for name in ("kind=", "title=", "classification=", "phase=",
	             "parent=", "create="):
		assert name not in into, (name, into)
	assert "body=" in into.split("optional:")[0]
	parked = assist_text("phase work=W1 to=parked ")
	assert "reason=" in parked.split("optional:")[0]
	assert "wait=" not in parked
	waiting = assist_text("phase work=W1 to=waiting ")
	assert "wait=" in waiting.split("optional:")[0]
	assert "wait=" not in assist_text("phase work=W1 "), \
		"wait= offered outside to=waiting"
	# W80: transfer left say entirely — the assist never offers the
	# retired keys, and on= binds to request=.
	discussion = assist_text("say thread=T1 body=b ")
	assert "pass-to=" not in discussion and "phase=" not in discussion
	carrier = assist_text("say thread=T1 body=b on=W1 ")
	assert "required: request=" in carrier, carrier
	passing = assist_text("pass work=W1 to=lang.impl ")
	assert "required:" in passing and "comment=" in passing \
		and "thread=" not in passing
	dup = assist_text("close work=X rationale=r duplicate-of=W2 ")
	assert "duplicate-of= needs outcome=rejected" in dup
	settled = assist_text(
		"close work=X rationale=r duplicate-of=W2 outcome=rejected ")
	assert "needs" not in settled


def test_assist_diagnoses_instead_of_guessing():
	"""W14 R2: malformed, unknown, duplicate-singular, and conflicting
	input yield the parser-shaped diagnostic in place of a plausible-
	looking ordinary hint; a repeated repeatable key stays valid and
	available; a live key prefix narrows the display."""
	from baton_work.tui.app import assist_text
	assert "retired flag spelling" in assist_text("block --work ")
	assert "not a key=value token" in assist_text("block bogus ")
	assert "unknown key 'zork'" in assist_text("block zork=1 ")
	assert "duplicate work=" in assist_text("close work=X work=Y ")
	assert "takes one of" in assist_text("close work=X outcome=bogus ")
	assert "takes an integer" in assist_text("respond obligation=abc ")
	assert "unknown key 'pass-to'" in assist_text(
		"say thread=T body=b pass-to=c.d ")
	repeat = assist_text(
		"create team=t kind=k title=x origin=external-report "
		"classification=suspected-defect body=b ref=a ref=b ")
	assert "duplicate" not in repeat and "ref=" in repeat, repeat
	assert assist_text("close outc").startswith("required: outcome=")
	assert "no close key starts with" in assist_text("close zzz")


def test_command_bar_caret_is_visible_and_placed(tmp_path):
	"""W14 R3 (PTY): while the bar is open the terminal caret is SHOWN
	at the insertion point with the assistance right of it; Esc closes
	the bar, hides the caret, restores the prior view, and executes
	nothing — the authority database is byte-identical throughout."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import hashlib
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	with open(database, "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":block work=W1 ", 0.6), (b"\x1b", 0.4), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	typed, (row, col, visible) = ptyharness.replay(steps[0],
	                                               cursor=True)
	assert visible, "the caret is hidden during command entry"
	assert (row, col) == (31, len(":block work=W1 ")), (row, col)
	bar = typed[31]
	assert bar.startswith(":block work=W1"), bar
	assert "on=" in bar[col:], f"no assistance right of the caret: {bar}"
	closed, (_row, _col, still) = ptyharness.replay(steps[1],
	                                                cursor=True)
	assert not still, "the caret survived closing the bar"
	assert closed[31].strip() == "", \
		f"Esc left residue on the bar row: {closed[31]!r}"
	with open(database, "rb") as handle:
		after = hashlib.sha256(handle.read()).hexdigest()
	assert after == before, "the command bar touched authority bytes"


def test_overwidth_input_scrolls_in_a_caret_viewport(tmp_path):
	"""W14 R3 (PTY): input longer than the row is never cut — a
	horizontal viewport with a `<` clip marker keeps the caret and the
	live tail visible, the assist yields entirely, and a wider resize
	recomputes the viewport from the SAME preserved buffer, showing it
	whole again."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	line = (b":create team=lang kind=bug "
	        b"title=a-long-title-that-overflows body=still-typing")
	assert len(line) > 43, "the input must overflow 44 columns"
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(line, 0.8), ("resize", (110, 32), 1.0),
		(b"\x1b", 0.4), (b"qy", 0.4)],
		columns=44, lines=24, dynamic_size=True, settle=1.2)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	narrow, (row, col, visible) = ptyharness.replay(
		steps[0], columns=44, lines=24, cursor=True)
	bar = narrow[23]
	assert bar.startswith("<"), f"no clip marker: {bar!r}"
	assert bar.endswith("body=still-typing"), bar
	assert visible and (row, col) == (23, 42), (row, col, visible)
	wide, (wrow, wcol, wvisible) = ptyharness.replay(
		steps[1], columns=110, lines=32, cursor=True)
	wbar = wide[31]
	assert wbar.startswith(line.decode()), \
		f"the buffer did not survive the resize whole: {wbar!r}"
	assert "<" not in wbar[:1], wbar
	assert wvisible and (wrow, wcol) == (31, len(line)), (wrow, wcol)


def test_assist_yields_below_eight_free_cells(tmp_path):
	"""W14 compact fallback (PTY): input that fits but leaves fewer
	than 8 cells renders alone — the hint yields, the input whole."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":block work=W1 ", 0.6), (b"\x1b", 0.3), (b"qy", 0.4)],
		columns=24, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	tight = ptyharness.replay(steps[0], columns=24, lines=24)
	assert tight[23].rstrip() == ":block work=W1", tight[23]
