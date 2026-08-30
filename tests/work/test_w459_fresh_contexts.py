"""W459: every managed start mints fresh agent contexts.

`work/records/2026/08/finding-fresh-agent-context-per-start/`. A Codex
Thread or an ACP session is replaceable runtime state, not deployment
configuration and not authority. The stable identity is the Baton
participant; the context behind it is rebuilt from canonical state,
accepted role instructions, and the bound dossier.

Carrying one across a restart carried everything with it — obsolete
binary and config paths baked into the thread, conversational
assumptions that no longer match the tree, and an old writer that might
still believe it holds work. So the launcher mints the locator, records
it under the private `run/` state, and hands it to the services of THAT
start.

This is the first slice: the mechanism in `tools/infra.py`. What it
holds is that a start mints, records privately, substitutes into the
services that need it, never adopts an older context, and leaves
nothing reusable behind when it fails.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
CONTROLLER = os.path.join(REPO, "tools", "infra.py")

pytestmark = pytest.mark.skipif(not os.path.isdir("/proc"),
                                reason="needs /proc")


def _fake_service(path):
	"""A service that stays up and records the argv it was launched
	with — which is how these tests read what was substituted."""
	path.write_text('''
import argparse, json, os, signal, sys, time
parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--record", required=True)
parser.add_argument("--saw", default="")
options = parser.parse_args()
with open(options.record, "a", encoding="utf-8") as handle:
    handle.write(json.dumps({"name": options.name, "saw": options.saw,
                             "env": os.environ.get("BATON_CONTEXT", "")}) + "\\n")
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True:
    time.sleep(0.02)
''', encoding="utf-8")
	return str(path)


def _fake_bootstrap(path):
	"""A context command in the shape of `--start-thread`: it prints
	one JSON locator and exits."""
	path.write_text('''
import argparse, json, sys, uuid
parser = argparse.ArgumentParser()
parser.add_argument("--participant", required=True)
parser.add_argument("--counter", required=True)
parser.add_argument("--fail", action="store_true")
parser.add_argument("--garbage", action="store_true")
parser.add_argument("--silent", action="store_true")
options = parser.parse_args()
if options.fail:
    sys.stderr.write("bootstrap refused\\n")
    raise SystemExit(3)
if options.garbage:
    sys.stdout.write("not json at all\\n")
    raise SystemExit(0)
if options.silent:
    sys.stdout.write(json.dumps({"participant": options.participant}) + "\\n")
    raise SystemExit(0)
with open(options.counter, "a", encoding="utf-8") as handle:
    handle.write("x")
with open(options.counter, encoding="utf-8") as handle:
    nth = len(handle.read())
sys.stdout.write(json.dumps({
    "threadId": f"thread-{nth}-{uuid.uuid4().hex[:8]}",
    "participant": options.participant,
    "role": "tuner",
    "configurationGeneration": 4}) + "\\n")
''', encoding="utf-8")
	return str(path)


@pytest.fixture()
def rig(tmp_path):
	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	return {
		"mailbox": mailbox,
		"service": _fake_service(tmp_path / "service.py"),
		"bootstrap": _fake_bootstrap(tmp_path / "bootstrap.py"),
		"record": str(tmp_path / "launched.jsonl"),
		"counter": str(tmp_path / "counter"),
		"tmp": tmp_path,
	}


def _write(rig, document):
	(rig["mailbox"] / "infra.json").write_text(
		json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _run(command, rig):
	return subprocess.run(
		[sys.executable, CONTROLLER, command, str(rig["mailbox"])],
		capture_output=True, text=True, timeout=20)


def _json(done):
	return json.loads(done.stdout if done.stdout else done.stderr)


def _state(rig):
	return json.loads((rig["mailbox"] / "run" / "infra-state.json")
	                  .read_text(encoding="utf-8"))


def _launched(rig):
	path = rig["record"]
	if not os.path.exists(path):
		return []
	with open(path, encoding="utf-8") as handle:
		return [json.loads(line) for line in handle if line.strip()]


def _manifest(rig, *, contexts=None, saw="{{context.tuner.threadId}}",
              env=None, renders=None, service_extra=()):
	service = {
		"name": "worker",
		"command": [sys.executable, rig["service"], "--name", "worker",
		            "--record", rig["record"], "--saw", saw,
		            *service_extra],
		"readiness": {"type": "process", "stableMilliseconds": 100},
		"startTimeoutSeconds": 4,
		"stopTimeoutSeconds": 2,
	}
	if env:
		service["env"] = env
	if renders:
		service["renders"] = renders
	document = {
		"version": 1,
		"startTimeoutSeconds": 4,
		"stopTimeoutSeconds": 2,
		"services": [service],
	}
	document["contexts"] = contexts if contexts is not None else [{
		"name": "tuner",
		"participant": "baton.tuner",
		"command": [sys.executable, rig["bootstrap"],
		            "--participant", "baton.tuner",
		            "--counter", rig["counter"]],
		"timeoutSeconds": 10,
	}]
	return document


def _started(rig, document=None):
	_write(rig, document or _manifest(rig))
	done = _run("start", rig)
	assert done.returncode == 0, done.stdout + done.stderr
	return _json(done)


# -- a start mints ------------------------------------------------------------

def test_a_start_mints_a_context_and_hands_it_to_the_service(rig):
	_started(rig)
	try:
		minted = _state(rig)["contexts"]["tuner"]
		assert minted["threadId"].startswith("thread-1-")
		assert minted["participant"] == "baton.tuner"
		assert minted["mintedAt"]
		saw = _launched(rig)[0]["saw"]
		assert saw == minted["threadId"], (saw, minted)
	finally:
		_run("stop", rig)


def test_the_locator_lives_in_private_run_state_only(rig):
	_started(rig)
	try:
		state = rig["mailbox"] / "run" / "infra-state.json"
		assert oct(state.stat().st_mode & 0o777) == "0o600"
		# and nothing durable in the mailbox was rewritten to hold it
		manifest = (rig["mailbox"] / "infra.json").read_text(
			encoding="utf-8")
		assert "thread-1-" not in manifest, \
			"the operator's deployment JSON was edited to carry a locator"
		assert "{{context.tuner.threadId}}" in manifest
	finally:
		_run("stop", rig)


def test_a_second_start_mints_a_different_context(rig):
	"""The decision itself: restarting with UNCHANGED configuration
	still creates a fresh context, never the previous one."""
	_started(rig)
	first = _state(rig)["contexts"]["tuner"]["threadId"]
	assert _run("stop", rig).returncode == 0
	_started(rig)
	try:
		second = _state(rig)["contexts"]["tuner"]["threadId"]
		assert second != first, (first, second)
		assert second.startswith("thread-2-")
		saw = [entry["saw"] for entry in _launched(rig)]
		assert saw == [first, second], saw
	finally:
		_run("stop", rig)


def test_the_participant_identity_is_what_stays_stable(rig):
	_started(rig)
	first = _state(rig)["contexts"]["tuner"]
	assert _run("stop", rig).returncode == 0
	_started(rig)
	try:
		second = _state(rig)["contexts"]["tuner"]
		assert first["participant"] == second["participant"] == "baton.tuner"
		assert first["threadId"] != second["threadId"]
	finally:
		_run("stop", rig)


# -- substitution -------------------------------------------------------------

def test_a_placeholder_resolves_in_env_as_well_as_argv(rig):
	_started(rig, _manifest(rig, env={"BATON_CONTEXT":
	                                  "id={{context.tuner.threadId}}"}))
	try:
		entry = _launched(rig)[0]
		assert entry["env"] == f"id={entry['saw']}", entry
	finally:
		_run("stop", rig)


def test_a_rendered_file_carries_the_fresh_locator(rig):
	"""How a component that reads a config FILE — the Codex dispatcher
	does — gets this start's locators without learning a new flag."""
	template = rig["tmp"] / "dispatcher.json.tmpl"
	template.write_text(json.dumps(
		{"targets": {"baton-tuner": {"threadId":
		                             "{{context.tuner.threadId}}"}}}),
		encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_started(rig, document)
	try:
		path = _launched(rig)[0]["saw"]
		assert path.startswith(str(rig["mailbox"] / "run" / "context"))
		assert oct(os.stat(path).st_mode & 0o777) == "0o600"
		body = json.loads(open(path, encoding="utf-8").read())
		minted = _state(rig)["contexts"]["tuner"]["threadId"]
		assert body["targets"]["baton-tuner"]["threadId"] == minted
		# the operator's template is untouched
		assert "{{context.tuner.threadId}}" in template.read_text(
			encoding="utf-8")
	finally:
		_run("stop", rig)


def test_a_rendered_file_is_replaced_on_the_next_start(rig):
	template = rig["tmp"] / "dispatcher.json.tmpl"
	template.write_text('{"id": "{{context.tuner.threadId}}"}',
	                    encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_started(rig, document)
	path = _launched(rig)[0]["saw"]
	first = json.loads(open(path, encoding="utf-8").read())["id"]
	assert _run("stop", rig).returncode == 0
	_started(rig, document)
	try:
		second = json.loads(open(path, encoding="utf-8").read())["id"]
		assert second != first, "a restart reused the rendered locator"
	finally:
		_run("stop", rig)


# -- refusals -----------------------------------------------------------------

def test_a_placeholder_naming_no_context_refuses_before_anything_starts(rig):
	_write(rig, _manifest(rig, saw="{{context.ghost.threadId}}"))
	done = _run("start", rig)
	assert done.returncode != 0
	assert "unknown context" in (done.stdout + done.stderr)
	assert _launched(rig) == [], "a service launched anyway"


def test_a_render_template_cannot_hide_an_unknown_context_until_launch(rig):
	"""A template is part of the service configuration just like argv.
	Its placeholders must be checked before an unrelated predecessor is
	allowed to launch."""
	template = rig["tmp"] / "dispatcher.json.tmpl"
	template.write_text('{"id": "{{context.ghost.threadId}}"}',
	                    encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	worker = document["services"][0]
	first = copy.deepcopy(worker)
	first["name"] = "first"
	first["command"][first["command"].index("worker")] = "first"
	first["command"][-1] = "literal"
	first.pop("renders")
	worker["after"] = ["first"]
	document["services"] = [first, worker]
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "did not mint" in (done.stdout + done.stderr)
	assert _launched(rig) == [], \
		"the template placeholder was discovered only after launch"


def test_a_service_cannot_run_before_the_context_it_references(rig):
	"""Context/service ordering is one graph, even though the manifest
	keeps the declarations in two arrays. A cycle across that boundary
	must refuse at load; discovering it after an unrelated service has
	started violates the controller's pre-flight guarantee."""
	document = _manifest(rig)
	worker = document["services"][0]
	first = copy.deepcopy(worker)
	first["name"] = "first"
	first["command"][first["command"].index("worker")] = "first"
	first["command"][-1] = "literal"
	worker["after"] = ["first"]
	late = copy.deepcopy(worker)
	late["name"] = "late"
	late["command"][late["command"].index("worker")] = "late"
	late["command"][-1] = "literal"
	late["after"] = ["worker"]
	document["services"] = [first, worker, late]
	document["contexts"][0]["after"] = ["late"]
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert _launched(rig) == [], \
		"the cross context/service cycle was discovered only after launch"


def test_a_render_nobody_references_refuses(rig):
	template = rig["tmp"] / "t.tmpl"
	template.write_text("{}", encoding="utf-8")
	_write(rig, _manifest(
		rig, renders=[{"name": "unused", "template": str(template)}]))
	done = _run("start", rig)
	assert done.returncode != 0
	assert "never references it" in (done.stdout + done.stderr)


def test_two_contexts_cannot_claim_one_participant(rig):
	document = _manifest(rig, contexts=[
		{"name": "one", "participant": "baton.tuner",
		 "command": [sys.executable, rig["bootstrap"], "--participant",
		             "baton.tuner", "--counter", rig["counter"]]},
		{"name": "two", "participant": "baton.tuner",
		 "command": [sys.executable, rig["bootstrap"], "--participant",
		             "baton.tuner", "--counter", rig["counter"]]}])
	document["services"][0]["command"][-1] = "{{context.one.threadId}}"
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "mints more than one context" in (done.stdout + done.stderr)


@pytest.mark.parametrize("flag,expected", [
	("--fail", "without minting anything"),
	("--garbage", "no readable JSON locator"),
	("--silent", "printed no usable threadId"),
])
def test_a_context_that_cannot_mint_fails_the_start(rig, flag, expected):
	"""A start that cannot mint a fresh context must not fall back on
	an older one — it must not start at all."""
	document = _manifest(rig, contexts=[{
		"name": "tuner", "participant": "baton.tuner",
		"command": [sys.executable, rig["bootstrap"], "--participant",
		            "baton.tuner", "--counter", rig["counter"], flag]}])
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0, done.stdout
	assert expected in (done.stdout + done.stderr), done.stdout + done.stderr
	assert _launched(rig) == []
	assert not (rig["mailbox"] / "run" / "infra-state.json").exists(), \
		"a failed start left lifecycle state behind"


def test_an_empty_thread_id_is_not_a_locator(rig):
	bootstrap = rig["tmp"] / "empty-bootstrap.py"
	bootstrap.write_text(
		'import json\nprint(json.dumps({"threadId": ""}))\n',
		encoding="utf-8")
	document = _manifest(rig, contexts=[{
		"name": "tuner", "participant": "baton.tuner",
		"command": [sys.executable, str(bootstrap)]}])
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert _launched(rig) == []


def test_a_failed_start_leaves_no_reusable_rendered_context(rig):
	"""The cleanup that matters: a half-start must not leave a file the
	NEXT start could read a stale locator out of."""
	template = rig["tmp"] / "dispatcher.json.tmpl"
	template.write_text('{"id": "{{context.tuner.threadId}}"}',
	                    encoding="utf-8")
	good = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_started(rig, good)
	path = _launched(rig)[0]["saw"]
	assert os.path.exists(path)
	assert _run("stop", rig).returncode == 0

	# now a start that cannot mint at all
	broken = _manifest(rig, contexts=[{
		"name": "tuner", "participant": "baton.tuner",
		"command": [sys.executable, rig["bootstrap"], "--participant",
		            "baton.tuner", "--counter", rig["counter"], "--fail"]}],
		saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_write(rig, broken)
	assert _run("start", rig).returncode != 0
	assert not os.path.exists(path), \
		"the abandoned start left its rendered locator readable"


def test_an_unreadable_render_template_refuses(rig):
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher",
		          "template": str(rig["tmp"] / "absent.tmpl")}])
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "cannot read render template" in (done.stdout + done.stderr)
	assert _launched(rig) == []


def test_a_render_target_cannot_follow_a_symlink(rig):
	"""Rendered state is controller-owned just like its lock, state and
	logs. A context command or same-user race must not turn O_TRUNC into
	an overwrite outside the coordination home."""
	victim = rig["tmp"] / "victim.json"
	victim.write_text("do not replace\n", encoding="utf-8")
	target = rig["mailbox"] / "run" / "context" / "dispatcher.json"
	bootstrap = rig["tmp"] / "link-bootstrap.py"
	bootstrap.write_text('''
import json, os, pathlib, sys
target, victim = sys.argv[1:]
pathlib.Path(target).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
os.symlink(victim, target)
print(json.dumps({"threadId": "thread-one"}))
''', encoding="utf-8")
	template = rig["tmp"] / "dispatcher.json.tmpl"
	template.write_text('{"id": "{{context.tuner.threadId}}"}',
	                    encoding="utf-8")
	document = _manifest(
		rig,
		contexts=[{"name": "tuner", "participant": "baton.tuner",
		           "command": [sys.executable, str(bootstrap), str(target),
		                       str(victim)]}],
		saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert victim.read_text(encoding="utf-8") == "do not replace\n"


# -- the rest of the controller is unchanged ---------------------------------

def test_a_manifest_with_no_contexts_still_starts(rig):
	document = _manifest(rig, contexts=[], saw="literal")
	_write(rig, document)
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		assert _json(done)["healthy"] is True
		assert _state(rig)["contexts"] == {}
		assert _launched(rig)[0]["saw"] == "literal"
	finally:
		_run("stop", rig)


def test_stop_still_owns_and_rolls_back_what_it_started(rig):
	_started(rig)
	pid = _state(rig)["services"]["worker"]["pid"]
	done = _run("stop", rig)
	assert done.returncode == 0, done.stdout + done.stderr
	assert not (rig["mailbox"] / "run" / "infra-state.json").exists()
	assert not os.path.exists(f"/proc/{pid}"), "the service outlived stop"


def test_the_setup_documentation_teaches_the_context_surface():
	import pathlib
	body = (pathlib.Path(REPO) / "docs" / "BATON-SETUP.md").read_text(
		encoding="utf-8")
	prose = " ".join(body.split())
	assert '"contexts"' in prose, "the manifest surface is undocumented"
	assert "{{context.NAME.FIELD}}" in prose
	assert "{{render.NAME}}" in prose
	assert "run/context" in prose
	# the decision itself, not just the syntax
	assert "minted by the start that uses it" in prose


def test_a_template_referencing_a_late_context_refuses_at_load(rig):
	"""Round 2's rule, on the ordering half rather than the existence
	half: a template may not reach a context that is not minted until
	after its own service has started."""
	template = rig["tmp"] / "d.tmpl"
	template.write_text('{"id": "{{context.tuner.threadId}}"}',
	                    encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	document["contexts"][0]["after"] = ["worker"]
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "waits for worker" in (done.stdout + done.stderr)
	assert _launched(rig) == []


def test_a_render_cannot_be_built_from_another_render(rig):
	template = rig["tmp"] / "d.tmpl"
	template.write_text('{"other": "{{render.second}}"}', encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "cannot be built from another render" in (
		done.stdout + done.stderr)


def test_the_render_uses_the_body_validated_at_load(rig):
	"""Rendering re-read the template at launch, which reintroduced the
	race preflight had just removed: the file could change between the
	check and the write. The body checked is the body written."""
	template = rig["tmp"] / "d.tmpl"
	template.write_text('{"id": "{{context.tuner.threadId}}"}',
	                    encoding="utf-8")
	document = _manifest(
		rig, saw="{{render.dispatcher}}",
		renders=[{"name": "dispatcher", "template": str(template)}])
	# a context command that rewrites the template AFTER load, before
	# the service that renders it launches
	document["contexts"][0]["command"] = [
		sys.executable, "-c",
		"import json,sys;"
		f"open({str(template)!r}, 'w').write('{{\"id\": \"tampered\"}}');"
		"sys.stdout.write(json.dumps({'threadId': 'thread-9'}))"]
	_write(rig, document)
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		path = _launched(rig)[0]["saw"]
		body = json.loads(open(path, encoding="utf-8").read())
		assert body["id"] == "thread-9", \
			"the render re-read the template instead of the validated body"
	finally:
		_run("stop", rig)


# -- slice 2: the shipped deployment contract --------------------------------

def test_the_example_manifest_mints_a_context_per_codex_participant():
	"""The deployment contract itself, not just the mechanism: the
	shipped example must not name a Thread id anywhere."""
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	contexts = {entry["name"]: entry for entry in example["contexts"]}
	assert set(contexts) == {"prompt", "reviewer", "tuner"}, sorted(contexts)
	assert {entry["participant"] for entry in contexts.values()} == \
		{"baton.prompt", "baton.codex", "baton.tuner"}
	for entry in contexts.values():
		assert "--start-thread" in entry["command"], entry["name"]
		assert entry["after"] == ["codex-app-server"], entry["name"]
		# the role is named, never inferred
		assert "--role" in entry["command"], entry["name"]
	assert contexts["prompt"]["command"][-1] == "prompt"


def test_the_example_dispatcher_reads_a_rendered_config():
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	dispatcher = next(service for service in example["services"]
	                  if service["name"] == "codex-dispatcher")
	assert "{{render.dispatcher}}" in dispatcher["command"]
	assert [entry["name"] for entry in dispatcher["renders"]] == \
		["dispatcher"]


def test_the_shipped_template_carries_placeholders_not_locators():
	body = open(os.path.join(REPO, "conf",
	                         "codex-event-bridge.template.json"),
	            encoding="utf-8").read()
	document = json.loads(body.replace("{{context.prompt.threadId}}", "p")
	                      .replace("{{context.reviewer.threadId}}", "a")
	                      .replace("{{context.tuner.threadId}}", "b"))
	targets = document["targets"]
	assert targets["baton-prompt"]["threadId"] == "p"
	assert targets["baton-reviewer"]["threadId"] == "a"
	assert targets["baton-tuner"]["threadId"] == "b"
	assert targets["baton-prompt"]["identity"] == {
		"participant": "baton.prompt",
		"role": "prompt",
		"actionOwner": "baton.slaw",
	}
	assert targets["baton-reviewer"]["identity"]["participant"] == \
		"baton.codex"
	assert targets["baton-tuner"]["identity"]["participant"] == \
		"baton.tuner"
	# and nothing that looks like a durable locator survives in it
	assert "019c0000" not in body, \
		"the template still carries a hard-coded Thread id"


def test_the_example_and_the_template_agree_on_context_names():
	"""The one way this pair can be wrong without either half looking
	wrong on its own."""
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	body = open(os.path.join(REPO, "conf",
	                         "codex-event-bridge.template.json"),
	            encoding="utf-8").read()
	declared = {entry["name"] for entry in example["contexts"]}
	referenced = set(re.findall(r"\{\{context\.([a-z-]+)\.", body))
	assert referenced == declared, (referenced, declared)


def test_prompt_is_a_dispatcher_target_without_a_readiness_producer():
	"""The human-attached Prompt thread is addressable, but it never
	competes with the managed reviewer's readiness consumer."""
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	body = open(os.path.join(REPO, "conf",
	                         "codex-event-bridge.template.json"),
	            encoding="utf-8").read()
	document = json.loads(body.replace("{{context.prompt.threadId}}", "p")
	                      .replace("{{context.reviewer.threadId}}", "a")
	                      .replace("{{context.tuner.threadId}}", "b"))
	assert document["targets"]["baton-prompt"]["identity"]["participant"] == \
		"baton.prompt"
	producers = [service for service in example["services"]
	             if service.get("participant")]
	assert [service["participant"] for service in producers].count(
		"baton.prompt") == 0
	assert [service["participant"] for service in producers].count(
		"baton.codex") == 1
	assert [service["participant"] for service in producers].count(
		"baton.tuner") == 1
	assert [service["participant"] for service in producers].count(
		"baton.claude") == 1
	assert [service["participant"] for service in producers].count(
		"baton.gemini") == 1


def test_the_release_ships_the_template_beside_the_manifest():
	"""A release with one and not the other ships a manifest that
	cannot load."""
	body = open(os.path.join(REPO, "tools", "deploy_work.py"),
	            encoding="utf-8").read()
	assert "conf/codex-event-bridge.template.json" in body, \
		"the deployer does not ship the render template"


# -- the ACP half: a fresh selection location per start ----------------------

def test_two_starts_give_a_service_different_start_ids(rig):
	"""W459 over W27 at the MANAGED restart boundary: each start hands
	its participants a location of their own, so a `new` session is
	genuinely new without weakening W27's refusal or deleting the
	selection the previous start published."""
	document = _manifest(rig, contexts=[], saw="state/{{start.id}}/x")
	_write(rig, document)
	assert _run("start", rig).returncode == 0
	first = _state(rig)["startId"]
	assert _run("stop", rig).returncode == 0
	assert _run("start", rig).returncode == 0
	try:
		second = _state(rig)["startId"]
		assert second != first, (first, second)
		saw = [entry["saw"] for entry in _launched(rig)]
		assert saw == [f"state/{first}/x", f"state/{second}/x"], saw
	finally:
		_run("stop", rig)


def test_the_start_id_is_recorded_and_shaped(rig):
	document = _manifest(rig, contexts=[], saw="{{start.id}}")
	_write(rig, document)
	assert _run("start", rig).returncode == 0
	try:
		start_id = _state(rig)["startId"]
		assert re.fullmatch(r"[0-9a-f]{32}", start_id), start_id
		assert _launched(rig)[0]["saw"] == start_id
		# status still recognises the service it launched
		done = _run("status", rig)
		assert _json(done)["services"][0]["state"] == "healthy", done.stdout
	finally:
		_run("stop", rig)


def test_the_start_id_reaches_a_render_template(rig):
	template = rig["tmp"] / "acp.tmpl"
	template.write_text('{"stateDir": "/state/{{start.id}}/baton.claude"}',
	                    encoding="utf-8")
	document = _manifest(
		rig, contexts=[], saw="{{render.acp}}",
		renders=[{"name": "acp", "template": str(template)}])
	_write(rig, document)
	assert _run("start", rig).returncode == 0
	try:
		body = json.loads(open(_launched(rig)[0]["saw"],
		                       encoding="utf-8").read())
		assert body["stateDir"] == \
			f"/state/{_state(rig)['startId']}/baton.claude"
	finally:
		_run("stop", rig)


def test_the_example_preserves_both_per_start_acp_configurations():
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	services = {service["name"]: service for service in example["services"]}
	for agent in ("claude", "gemini"):
		name = f"{agent}-acp"
		service = services[name]
		assert service["participant"] == f"baton.{agent}"
		assert f"{{{{render.{name}}}}}" in service["command"]
		template = f"acp-{agent}.template.json"
		assert service["requires"] == [f"/absolute/path/to/{template}"]
		body = open(os.path.join(REPO, "conf", template),
		            encoding="utf-8").read()
		document = json.loads(body.replace("{{start.id}}", "S"))
		assert document["baton"]["participant"] == f"baton.{agent}"
		assert "/S/" in document["stateDir"], document["stateDir"]
		# W27 is not weakened: the mode stays `new`, and it is the LOCATION
		# that is fresh rather than the refusal that is removed.
		assert document["session"]["mode"] == "new"


def test_the_fresh_rollout_preserves_both_deployment_owned_acp_inputs():
	root = os.path.join(
		REPO, "work", "records", "2026", "08",
		"finding-interactive-prompt-participant", "evidence",
		"schema-27-fresh")
	infra = json.loads(open(os.path.join(root, "infra.template.json"),
	                        encoding="utf-8").read())
	services = {service["name"]: service for service in infra["services"]}
	for agent in ("claude", "gemini"):
		name = f"{agent}-acp"
		service = services[name]
		assert service["participant"] == f"baton.{agent}"
		assert service["requires"] == [
			f"{{{{home}}}}/acp-{agent}.template.json"]
		assert service["renders"] == [{
			"name": name,
			"template": f"{{{{home}}}}/acp-{agent}.template.json",
		}]
		document = json.loads(open(
			os.path.join(root, f"acp-{agent}.template.json"),
			encoding="utf-8").read())
		assert document["baton"]["participant"] == f"baton.{agent}"
		assert document["stateDir"] == \
			f"{{{{runtime}}}}/acp/{{{{start.id}}}}/baton.{agent}"
		assert document["session"]["mode"] == "new"
	claude = json.loads(open(os.path.join(root, "acp-claude.template.json"),
	                         encoding="utf-8").read())
	assert set(claude["agent"]["env"]) == {
		"AGENT_REAL", "PROTECTED_PATHS_FILE", "CLAUDE_CONFIG_DIR"}
	assert len(claude["policyResources"]) == 5
	assert claude["permissionMode"] == "bypassPermissions"
	gemini = json.loads(open(os.path.join(root, "acp-gemini.template.json"),
	                         encoding="utf-8").read())
	assert "--admin-policy" in gemini["agent"]["args"]
	assert set(gemini["agent"]["env"]) == {
		"GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT_ID"}
	assert gemini["policyResources"] == ["{{gemini-policy}}"]
	assert gemini["permissionMode"] == "yolo"


def test_the_release_ships_every_lifecycle_template():
	body = open(os.path.join(REPO, "tools", "deploy_work.py"),
	            encoding="utf-8").read()
	for name in ("conf/codex-event-bridge.template.json",
	             "conf/acp-bridge.template.json",
	             "conf/acp-claude.template.json",
	             "conf/acp-gemini.template.json"):
		assert name in body, name


def test_every_acp_lifecycle_template_selects_the_two_hour_turn_deadline():
	for name in ("acp-bridge.template.json",
	             "acp-claude.template.json",
	             "acp-gemini.template.json"):
		document = json.loads(open(os.path.join(REPO, "conf", name),
		                           encoding="utf-8").read())
		assert document["turnTimeoutMs"] == 7200000, name


def test_the_setup_documentation_explains_the_acp_boundary():
	import pathlib
	prose = " ".join((pathlib.Path(REPO) / "docs" / "BATON-SETUP.md")
	                 .read_text(encoding="utf-8").split())
	assert "{{start.id}}" in prose
	assert "as history" in prose, \
		"the doc does not say the previous selection is preserved"


# -- slice 3: a managed two-start proof --------------------------------------
#
# What survives a restart and what does not, proved through the real
# controller against a real Baton authority. The vendor processes are
# stood in for — this gate runs no Codex app-server and no ACP agent —
# but everything Baton owns is genuine: the manifest loader, the
# minting, the rendering, the per-start identity, and the participant's
# own actionable-Work projection read through the public CLI.

def _acp_service(path):
	"""Stands in for the ACP bridge: it reads its RENDERED config,
	publishes a session selection where that config points, and asks
	Baton what it is supposed to be doing — which is the whole of what
	a restart must preserve."""
	path.write_text('''
import json, os, signal, subprocess, sys, time
config = json.load(open(sys.argv[sys.argv.index("--config") + 1]))
state = config["stateDir"]
os.makedirs(state, exist_ok=True)
selection = os.path.join(state, "session.json")
fresh = not os.path.exists(selection)
if fresh:
    with open(selection, "w") as handle:
        json.dump({"sessionId": "session-" + os.path.basename(
            os.path.dirname(state))}, handle)
env = dict(os.environ)
env["PYTHONPATH"] = config["srcDir"]
done = subprocess.run(
    [sys.executable, "-m", "baton_work.cli",
     "--config", config["baton"]["config"],
     "--participant", config["baton"]["participant"],
     "wait", "timeout=0"],
    capture_output=True, text=True, env=env, timeout=60)
actionable = json.loads(done.stdout)["result"]["actionable"]
with open(config["recordPath"], "a") as handle:
    handle.write(json.dumps({
        "stateDir": state,
        "freshSelection": fresh,
        "participant": config["baton"]["participant"],
        "work": sorted(entry.get("local_id") for entry in actionable
                       if entry["kind"] == "work"),
    }) + "\\n")
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True:
    time.sleep(0.02)
''', encoding="utf-8")
	return str(path)


@pytest.fixture()
def managed(rig, tmp_path):
	"""One real Baton authority, one Work routed to the participant,
	and a manifest that mints a Codex-shaped locator and renders a
	per-start ACP configuration."""
	sys.path.insert(0, os.path.join(REPO, "src"))
	import baton_work as bw
	import fixtures as fx
	from baton_work import transitions as tr

	(tmp_path / "home").mkdir(mode=0o700, exist_ok=True)
	config_path, database = fx.build_instance(
		str(tmp_path / "home"),
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the work that must survive",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")
	store.close()

	template = tmp_path / "acp.template.json"
	template.write_text(json.dumps({
		"baton": {"config": config_path, "participant": "lang.ada"},
		"srcDir": os.path.join(REPO, "src"),
		"recordPath": rig["record"],
		"stateDir": str(tmp_path / "acpstate" / "{{start.id}}" / "lang.ada"),
	}), encoding="utf-8")

	document = _manifest(rig, saw="unused")
	document["services"] = [{
		"name": "acp",
		"participant": "lang.ada",
		"command": [sys.executable, _acp_service(tmp_path / "acp.py"),
		            "--config", "{{render.acp}}"],
		"renders": [{"name": "acp", "template": str(template)}],
		"readiness": {"type": "process", "stableMilliseconds": 100},
		"startTimeoutSeconds": 6,
		"stopTimeoutSeconds": 2,
	}]
	_write(rig, document)
	return {"work": born["work_id"], "config": config_path}


def test_a_second_managed_start_changes_both_locators_and_keeps_the_work(
		rig, managed):
	"""The proof slice 3 owes: across two managed starts the
	participant identity and its actionable Work are the same, while
	the Codex-shaped locator and the ACP selection location are both
	different."""
	for _ in range(2):
		done = _run("start", rig)
		assert done.returncode == 0, done.stdout + done.stderr
		assert _run("stop", rig).returncode == 0

	first, second = _launched(rig)
	local = managed["work"].rsplit("-", 1)[1]

	# what SURVIVES
	assert first["participant"] == second["participant"] == "lang.ada"
	assert first["work"] == second["work"] == [local], (first, second)

	# what CHANGES
	assert first["stateDir"] != second["stateDir"], first["stateDir"]
	assert first["freshSelection"] is second["freshSelection"] is True, \
		"a managed start resumed the previous ACP selection"

	# the previous selection is history, not garbage
	previous = os.path.join(first["stateDir"], "session.json")
	assert os.path.exists(previous), \
		"the earlier start's selection was deleted rather than kept"
	assert json.loads(open(previous, encoding="utf-8").read())["sessionId"] \
		!= json.loads(open(os.path.join(second["stateDir"],
		                                "session.json"),
		                   encoding="utf-8").read())["sessionId"]


def test_the_two_starts_mint_different_codex_locators(rig, managed):
	"""The other half of the same restart: the Thread locator is
	replaced too, and by the start that uses it."""
	minted = []
	for _ in range(2):
		assert _run("start", rig).returncode == 0
		minted.append(_state(rig)["contexts"]["tuner"]["threadId"])
		assert _run("stop", rig).returncode == 0
	assert minted[0] != minted[1], minted
	assert all(value.startswith("thread-") for value in minted), minted


def test_the_setup_guide_documents_the_two_start_check():
	import pathlib
	prose = " ".join((pathlib.Path(REPO) / "docs" / "BATON-SETUP.md")
	                 .read_text(encoding="utf-8").split())
	assert "Proving a restart against real backends" in prose
	assert "What must CHANGE" in prose and "What must NOT" in prose
	assert "run/infra-state.json" in prose
