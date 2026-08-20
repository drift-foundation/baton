#!/usr/bin/env python3
"""Mailbox-local lifecycle controller for the configured v11 backend set.

The controller owns only processes it launched and can still identify through
Linux /proc start identity and argv. It never discovers, adopts, or kills a
process merely because a port, socket, name, or PID looks familiar.
"""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request


MANIFEST_NAME = "infra.json"
STATE_NAME = "infra-state.json"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
PARTICIPANT_RE = re.compile(r"^[^.\s]+\.[^.\s]+$")


class InfraError(Exception):
	pass


class StartupSignalGuard:
	"""Turn ordinary controller termination into a recorded rollback."""

	SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)

	def __init__(self):
		self.received = None
		self.previous = {}

	def __enter__(self):
		for signum in self.SIGNALS:
			self.previous[signum] = signal.getsignal(signum)
			signal.signal(signum, self._receive)
		return self

	def __exit__(self, _type, _value, _traceback):
		for signum, handler in self.previous.items():
			signal.signal(signum, handler)

	def _receive(self, signum, _frame):
		self.received = signum

	def check(self):
		if self.received is not None:
			raise InfraError(f"startup interrupted by signal {self.received}")


def _strict_object(pairs):
	result = {}
	for key, value in pairs:
		if key in result:
			raise InfraError(f"duplicate JSON key {key!r}")
		result[key] = value
	return result


def _read_json(path):
	"""Read one mailbox-owned JSON file under the same ownership
	discipline as the lock and the logs.

	Not named by the review, and NOT the same hole: `_load_state`
	already `lstat`s this path and refuses a symlink or a group-readable
	mode before reading. What it did not cover is a HARD link — which
	`lstat` cannot see — and the window between that check and the open.
	Going through the shared helper closes both, and the `lstat` guard
	stays because it is reached first and says plainly what is wrong.

	The write side needed nothing: a fresh `O_EXCL` temporary plus
	`os.replace` never follows a link at the destination."""
	try:
		fd = _open_owned(path, os.O_RDONLY, "lifecycle state")
	except InfraError:
		raise
	try:
		with os.fdopen(fd, encoding="utf-8") as handle:
			return json.load(handle, object_pairs_hook=_strict_object)
	except InfraError:
		raise
	except (OSError, json.JSONDecodeError) as error:
		raise InfraError(f"cannot read {path}: {error}") from error


def _object(value, where):
	if not isinstance(value, dict):
		raise InfraError(f"{where} must be an object")
	return value


def _keys(value, allowed, where):
	unknown = sorted(set(value) - set(allowed))
	if unknown:
		raise InfraError(f"{where} has unknown keys: {', '.join(unknown)}")


def _string(value, where):
	if not isinstance(value, str) or not value.strip() or "\0" in value:
		raise InfraError(f"{where} must be a non-empty string")
	return value


def _absolute(value, where):
	value = _string(value, where)
	if not os.path.isabs(value):
		raise InfraError(f"{where} must be an absolute path")
	return value


def _positive_integer(value, where):
	if not isinstance(value, int) or isinstance(value, bool) or value < 1:
		raise InfraError(f"{where} must be a positive integer")
	return value


def _string_array(value, where, *, absolute=False, unique=False):
	if not isinstance(value, list):
		raise InfraError(f"{where} must be an array")
	result = []
	for index, entry in enumerate(value):
		item = _absolute(entry, f"{where}[{index}]") if absolute \
			else _string(entry, f"{where}[{index}]")
		if unique and item in result:
			raise InfraError(f"{where} repeats {item!r}")
		result.append(item)
	return result


# W482: the readiness control exchange is ONE bounded newline-delimited
# JSON line each way. Bounded because a probe must fail closed rather
# than read forever from a service that is answering wrongly, and one
# line because the reply is a status and not a stream.
CONTROL_REPLY_LIMIT = 64 * 1024

# The whole exchange's budget, connect included. Short on purpose: a
# probe is asked again on the caller's retry loop, so the question a
# single probe answers is "is it ready NOW", never "will it be".
CONTROL_PROBE_SECONDS = 0.25


def _control_object(value, where):
	"""One JSON object of scalars for the readiness exchange.

	Scalars only, and no nesting: `expect` matches required TOP-LEVEL
	reply fields and this first version deliberately grows no
	expression language. A request that cannot be written as one line
	of JSON is not a readiness probe."""
	value = _object(value, where)
	for key, entry in value.items():
		if not isinstance(key, str) or not key:
			raise InfraError(f"{where} has an invalid field name {key!r}")
		if isinstance(entry, bool) or entry is None:
			continue
		if not isinstance(entry, (str, int, float)):
			raise InfraError(
				f"{where}.{key} must be a string, number, boolean or null")
	return dict(value)


def _readiness(raw, where):
	if raw is None:
		return {"type": "process", "stableMilliseconds": 250}
	raw = _object(raw, where)
	kind = _string(raw.get("type"), f"{where}.type")
	if kind == "process":
		_keys(raw, {"type", "stableMilliseconds"}, where)
		stable = _positive_integer(raw.get("stableMilliseconds", 250),
		                           f"{where}.stableMilliseconds")
		return {"type": kind, "stableMilliseconds": stable}
	if kind == "unix_socket":
		# W482 (finding-dispatcher-target-readiness): a connection is
		# the complete health contract for some services and a
		# half-truth for others. The Codex dispatcher begins listening
		# before its configured targets resume and keeps listening when
		# one is `notLoaded` — so during the 975af64 cutover `status`
		# reported healthy while a target could not resume at all, and
		# the readiness producer went on forwarding Work into a queue
		# nothing would drain.
		#
		# `request`/`expect` ASK it instead. Both together or neither:
		# a request with nothing to assert about the reply proves no
		# more than the connection did, and an expectation with no
		# request has nothing to read.
		_keys(raw, {"type", "path", "request", "expect"}, where)
		probe = {"type": kind, "path": _absolute(raw.get("path"),
		                                         f"{where}.path"),
		         "request": None, "expect": None}
		if ("request" in raw) != ("expect" in raw):
			raise InfraError(
				f"{where}.request and {where}.expect are configured "
				f"together or not at all")
		if "request" in raw:
			probe["request"] = _control_object(raw.get("request"),
			                                   f"{where}.request")
			probe["expect"] = _control_object(raw.get("expect"),
			                                  f"{where}.expect")
			if not probe["expect"]:
				raise InfraError(
					f"{where}.expect must assert at least one field; an "
					f"empty expectation proves nothing the connection "
					f"did not")
		return probe
	if kind == "http":
		_keys(raw, {"type", "url", "expectedStatus"}, where)
		url = _string(raw.get("url"), f"{where}.url")
		parsed = urllib.parse.urlparse(url)
		try:
			port = parsed.port
		except ValueError as error:
			raise InfraError(f"{where}.url has an invalid port") from error
		if parsed.scheme != "http" or parsed.hostname not in {
				"127.0.0.1", "localhost", "::1"} or not port:
			raise InfraError(f"{where}.url must be an explicit loopback http URL")
		expected = raw.get("expectedStatus", 200)
		if not isinstance(expected, int) or isinstance(expected, bool) \
				or not 100 <= expected <= 599:
			raise InfraError(f"{where}.expectedStatus must be an HTTP status")
		return {"type": kind, "url": url, "expectedStatus": expected}
	raise InfraError(f"{where}.type must be process, http, or unix_socket")


def load_manifest(mailbox):
	path = os.path.join(mailbox, MANIFEST_NAME)
	try:
		with open(path, "rb") as handle:
			encoded = handle.read()
	except OSError as error:
		raise InfraError(f"cannot read {path}: {error}") from error
	try:
		raw = json.loads(encoded, object_pairs_hook=_strict_object)
	except InfraError:
		raise
	except (UnicodeDecodeError, json.JSONDecodeError) as error:
		raise InfraError(f"cannot read {path}: {error}") from error
	raw = _object(raw, "manifest")
	_keys(raw, {"version", "startTimeoutSeconds", "stopTimeoutSeconds",
	            "contexts", "services"}, "manifest")
	if raw.get("version") != 1:
		raise InfraError("manifest.version must be exactly 1")
	start_timeout = _positive_integer(raw.get("startTimeoutSeconds", 15),
	                                  "manifest.startTimeoutSeconds")
	stop_timeout = _positive_integer(raw.get("stopTimeoutSeconds", 10),
	                                 "manifest.stopTimeoutSeconds")
	services_raw = raw.get("services")
	if not isinstance(services_raw, list) or not services_raw:
		raise InfraError("manifest.services must be a non-empty array")
	services = {}
	participants = set()
	input_order = []
	contexts, context_order = _contexts(raw.get("contexts", []))
	allowed = {"name", "command", "after", "cwd", "env", "requires",
	           "participant", "readiness", "startTimeoutSeconds",
	           "stopTimeoutSeconds", "renders"}
	for index, value in enumerate(services_raw):
		where = f"manifest.services[{index}]"
		value = _object(value, where)
		_keys(value, allowed, where)
		name = _string(value.get("name"), f"{where}.name")
		if not NAME_RE.fullmatch(name):
			raise InfraError(f"{where}.name must match {NAME_RE.pattern}")
		if name in services:
			raise InfraError(f"duplicate service name {name!r}")
		command = _string_array(value.get("command"), f"{where}.command")
		if not command:
			raise InfraError(f"{where}.command must not be empty")
		command[0] = _absolute(command[0], f"{where}.command[0]")
		after = _string_array(value.get("after", []), f"{where}.after",
		                      unique=True)
		cwd = value.get("cwd")
		if cwd is not None:
			cwd = _absolute(cwd, f"{where}.cwd")
		requires = _string_array(value.get("requires", []),
		                         f"{where}.requires", absolute=True,
		                         unique=True)
		env_raw = value.get("env", {})
		if not isinstance(env_raw, dict):
			raise InfraError(f"{where}.env must be an object")
		env = {}
		for key, entry in env_raw.items():
			if not isinstance(key, str) or not key or "=" in key or "\0" in key:
				raise InfraError(f"{where}.env has invalid name {key!r}")
			if not isinstance(entry, str) or "\0" in entry:
				raise InfraError(f"{where}.env.{key} must be a string")
			env[key] = entry
		participant = value.get("participant")
		if participant is not None:
			participant = _string(participant, f"{where}.participant")
			if not PARTICIPANT_RE.fullmatch(participant):
				raise InfraError(f"{where}.participant must be team.member")
			if participant in participants:
				raise InfraError(f"participant {participant} is assigned more than once")
			participants.add(participant)
		service_start = _positive_integer(
			value.get("startTimeoutSeconds", start_timeout),
			f"{where}.startTimeoutSeconds")
		service_stop = _positive_integer(
			value.get("stopTimeoutSeconds", stop_timeout),
			f"{where}.stopTimeoutSeconds")
		services[name] = {
			"name": name, "command": command, "after": after, "cwd": cwd,
			"env": env, "requires": requires, "participant": participant,
			"renders": _renders(value.get("renders", []), where),
			"readiness": _readiness(value.get("readiness"),
			                        f"{where}.readiness"),
			"startTimeoutSeconds": service_start,
			"stopTimeoutSeconds": service_stop,
		}
		input_order.append(name)
	for service in services.values():
		for dependency in service["after"]:
			if dependency not in services:
				raise InfraError(f"service {service['name']} depends on unknown service {dependency}")
			if dependency == service["name"]:
				raise InfraError(f"service {service['name']} depends on itself")
	order = []
	remaining = set(input_order)
	while remaining:
		ready = [name for name in input_order if name in remaining
		         and all(dependency in order for dependency
		                 in services[name]["after"])]
		if not ready:
			raise InfraError("service dependency graph contains a cycle")
		for name in ready:
			order.append(name)
			remaining.remove(name)
	manifest = {
		"path": path,
		"digest": hashlib.sha256(encoded).hexdigest(),
		"startTimeoutSeconds": start_timeout,
		"stopTimeoutSeconds": stop_timeout,
		"contexts": contexts,
		"contextOrder": context_order,
		"services": services,
		"order": order,
	}
	_check_references(manifest)
	return manifest


# W459 (finding-fresh-agent-context-per-start): a managed start MINTS
# the execution contexts its agents run in — Codex Threads today — and
# never inherits one from a previous start.
#
# The stable identity is the Baton participant; the Thread behind it is
# replaceable runtime state. Carrying one across a restart carried
# everything with it: obsolete binary and config paths baked into the
# thread's instructions, a conversation whose assumptions no longer
# match the tree, and an old writer that may still believe it holds
# work. So the locator is minted here, recorded under the private
# `run/` state, and referenced by the services that need it — an
# operator never edits a durable JSON file to rotate one.
#
# `{{context.NAME.FIELD}}` in a service's command, cwd, env value or
# requires resolves to a field of the context minted THIS START.
#
# `{{start.id}}` is this start's own identifier. Not every agent has a
# locator to mint: an ACP participant has a state DIRECTORY, and W27
# rules that a `new` run refuses when a selection is already there and
# a `load` run resumes it. Neither may be weakened — but a start that
# hands each participant its own fresh location gets a fresh session
# with W27 untouched, because absence is what `new` requires and the
# previous start's selection is left exactly where it was, as history.
# `{{render.NAME}}` resolves to a file this start wrote from a template
# with the same substitution applied — which is how a component that
# reads a config FILE (the Codex dispatcher does) gets fresh locators
# without learning a new argument.
PLACEHOLDER_RE = re.compile(r"\{\{(context\.[a-z][a-z0-9-]*\.[a-zA-Z][a-zA-Z0-9_]*"
                            r"|render\.[a-z][a-z0-9-]*"
                            r"|start\.id)\}\}")
CONTEXT_NAME_FIELD = "threadId"


def _contexts(raw):
	"""The per-start context declarations, in dependency order.

	A context is NOT a service: it is a short-lived command that must
	exit 0 and print one JSON object naming what it minted. It has no
	readiness, no pid to own and nothing to stop — what it leaves
	behind is a locator, and the process that uses the locator is the
	service."""
	if not isinstance(raw, list):
		raise InfraError("manifest.contexts must be an array")
	contexts = {}
	order = []
	participants = set()
	for index, value in enumerate(raw):
		where = f"manifest.contexts[{index}]"
		value = _object(value, where)
		_keys(value, {"name", "command", "after", "cwd", "env",
		              "requires", "participant", "timeoutSeconds"}, where)
		name = _string(value.get("name"), f"{where}.name")
		if not NAME_RE.fullmatch(name):
			raise InfraError(f"{where}.name must match {NAME_RE.pattern}")
		if name in contexts:
			raise InfraError(f"duplicate context name {name!r}")
		command = _string_array(value.get("command"), f"{where}.command")
		if not command:
			raise InfraError(f"{where}.command must not be empty")
		command[0] = _absolute(command[0], f"{where}.command[0]")
		cwd = value.get("cwd")
		if cwd is not None:
			cwd = _absolute(cwd, f"{where}.cwd")
		participant = value.get("participant")
		if participant is not None:
			participant = _string(participant, f"{where}.participant")
			if not PARTICIPANT_RE.fullmatch(participant):
				raise InfraError(f"{where}.participant must be team.member")
			if participant in participants:
				raise InfraError(
					f"participant {participant} mints more than one context")
			participants.add(participant)
		env_raw = value.get("env", {})
		if not isinstance(env_raw, dict):
			raise InfraError(f"{where}.env must be an object")
		for key, entry in env_raw.items():
			if not isinstance(key, str) or not key or "=" in key \
					or "\0" in key:
				raise InfraError(f"{where}.env has invalid name {key!r}")
			if not isinstance(entry, str) or "\0" in entry:
				raise InfraError(f"{where}.env.{key} must be a string")
		contexts[name] = {
			"name": name, "command": command,
			"after": _string_array(value.get("after", []),
			                       f"{where}.after", unique=True),
			"cwd": cwd, "env": dict(env_raw),
			"requires": _string_array(value.get("requires", []),
			                          f"{where}.requires", absolute=True,
			                          unique=True),
			"participant": participant,
			"timeoutSeconds": _positive_integer(
				value.get("timeoutSeconds", 120),
				f"{where}.timeoutSeconds"),
		}
		order.append(name)
	return contexts, order


def _renders(raw, where):
	"""Files this start writes from a template, with the minted context
	substituted in. Always written under `run/`, never over the
	operator's template."""
	if not isinstance(raw, list):
		raise InfraError(f"{where}.renders must be an array")
	out = []
	seen = set()
	for index, value in enumerate(raw):
		spot = f"{where}.renders[{index}]"
		value = _object(value, spot)
		_keys(value, {"name", "template"}, spot)
		name = _string(value.get("name"), f"{spot}.name")
		if not NAME_RE.fullmatch(name):
			raise InfraError(f"{spot}.name must match {NAME_RE.pattern}")
		if name in seen:
			raise InfraError(f"duplicate render name {name!r} in {where}")
		seen.add(name)
		template = _absolute(value.get("template"), f"{spot}.template")
		# W459 review round 2: read at LOAD, not at launch. A
		# placeholder hidden in a template used to escape preflight
		# entirely — the manifest passed, predecessor services
		# launched, and substitution failed with processes already
		# running. The body is kept so the render writes what was
		# VALIDATED, rather than re-reading a file that may have
		# changed in between.
		try:
			with open(template, "r", encoding="utf-8") as handle:
				body = handle.read()
		except (OSError, UnicodeDecodeError) as error:
			raise InfraError(
				f"cannot read render template {template}: {error}") from None
		out.append({"name": name, "template": template, "body": body})
	return out


def _placeholders(value):
	return set(PLACEHOLDER_RE.findall(value or ""))


def _service_strings(service):
	yield from service["command"]
	yield from service["requires"]
	yield from service["env"].values()
	if service["cwd"]:
		yield service["cwd"]


def _check_references(manifest):
	"""Every placeholder names something this start will actually have,
	and names it only after the start has it.

	Refusing at LOAD is the point: a manifest that would fail halfway
	through a launch, with processes already running, is a worse
	discovery than one that fails before anything starts."""
	renders = {}
	for service in manifest["services"].values():
		for entry in service["renders"]:
			if entry["name"] in renders:
				raise InfraError(
					f"duplicate render name {entry['name']!r} across services")
			renders[entry["name"]] = service["name"]
	for name in manifest["contextOrder"]:
		for dependency in manifest["contexts"][name]["after"]:
			if dependency not in manifest["services"]:
				raise InfraError(
					f"context {name} depends on unknown service {dependency}")
	# W459 review: services and context availability are ONE ordering
	# problem. Checking only that a context is declared let a manifest
	# through in which the context waited on a service launched AFTER
	# the one referencing it — preflight passed, the first service
	# started, and the launch then failed at substitution with
	# processes already running. That is precisely the
	# fail-before-launch guarantee this slice exists to give.
	#
	# A context is minted once every service in its `after` set has
	# started, so it is available to a service S if and only if all of
	# them come strictly BEFORE S in the launch order. A cycle spanning
	# both kinds of edge — S needs a context that waits on S, or on
	# anything after S — fails exactly this test, which is why it is
	# stated as ordering rather than as a separate cycle check.
	position = {name: index for index, name in enumerate(manifest["order"])}
	for name in manifest["order"]:
		service = manifest["services"][name]
		# W459 review round 2: template bodies are scanned with the
		# service's own fields, under the same rules. A context hidden
		# in a template is exactly as invalid as one named in an
		# argument, and finding it later — after predecessors have
		# launched — is the discovery this preflight exists to prevent.
		# `(text, where)`: the same rules, but the refusal says which
		# FILE to open when the placeholder came from a template.
		texts = [(text, f"service {name}")
		         for text in _service_strings(service)]
		for entry in service["renders"]:
			for token in _placeholders(entry["body"]):
				if token.startswith("render."):
					raise InfraError(
						f"service {name} render {entry['name']!r} "
						f"references {{{{{token}}}}}; a render cannot be "
						f"built from another render")
			texts.append((entry["body"],
			              f"service {name} render {entry['name']!r} "
			              f"({entry['template']})"))
		for text, where in texts:
			for token in _placeholders(text):
				kind, _, rest = token.partition(".")
				# `{{start.id}}` needs no check: it exists before
				# anything launches and names nothing the manifest has
				# to declare.
				if kind == "start":
					continue
				if kind == "context":
					context_name = rest.split(".", 1)[0]
					context = manifest["contexts"].get(context_name)
					if context is None:
						raise InfraError(
							f"{where} references unknown context "
							f"{context_name!r}, which this start did not "
							f"mint")
					late = [dependency for dependency in context["after"]
					        if position[dependency] >= position[name]]
					if late:
						raise InfraError(
							f"{where} references context "
							f"{context_name!r}, which waits for "
							f"{', '.join(sorted(late))} — not started "
							f"until {name} itself has, so the context "
							f"cannot exist when {name} needs it")
				elif rest not in renders:
					raise InfraError(
						f"service {name} references unknown render {rest!r}")
				elif renders[rest] != name:
					raise InfraError(
						f"service {name} references render {rest!r} declared "
						f"by service {renders[rest]}")
		for entry in service["renders"]:
			token = f"render.{entry['name']}"
			if not any(token in _placeholders(text)
			           for text in _service_strings(service)):
				raise InfraError(
					f"service {name} renders {entry['name']!r} and never "
					f"references it")


def _private_directory(path):
	try:
		os.mkdir(path, 0o700)
	except FileExistsError:
		pass
	except OSError as error:
		raise InfraError(f"cannot create private directory {path}: {error}") from error
	try:
		info = os.lstat(path)
	except OSError as error:
		raise InfraError(f"cannot inspect {path}: {error}") from error
	if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
		raise InfraError(f"{path} is not a real directory")
	if stat.S_IMODE(info.st_mode) & 0o077:
		raise InfraError(f"{path} is not private (mode {stat.S_IMODE(info.st_mode):04o})")


class MailboxLock:
	def __init__(self, mailbox):
		self.mailbox = mailbox
		self.run_dir = os.path.join(mailbox, "run")
		self.log_dir = os.path.join(mailbox, "log")
		self.handle = None

	def __enter__(self):
		_private_directory(self.run_dir)
		_private_directory(self.log_dir)
		path = os.path.join(self.run_dir, "infra.lock")
		# The lock is private lifecycle metadata under the same
		# containment contract as the state and the logs. Validated
		# BEFORE `fdopen` or `flock`, so a link to an unrelated file
		# cannot make this controller take its advisory lock on an inode
		# the mailbox does not own — which would let lifecycle commands
		# block behind, or interfere with, a lock domain that is not
		# theirs.
		fd = _open_owned(path, os.O_RDWR | os.O_CREAT, "lifecycle lock")
		self.handle = os.fdopen(fd, "r+")
		fcntl.flock(self.handle, fcntl.LOCK_EX)
		return self

	def __exit__(self, _type, _value, _traceback):
		if self.handle is not None:
			fcntl.flock(self.handle, fcntl.LOCK_UN)
			self.handle.close()


def _context_dir(mailbox):
	return os.path.join(mailbox, "run", "context")


def _mint_context(mailbox, context, signals):
	"""Run one context command and record what it minted.

	It must exit 0 and print ONE JSON object. Anything else is a
	refusal: a start that cannot mint a fresh context must not fall
	back on an older one, which is the whole decision this implements.
	"""
	signals.check()
	for path in context["requires"]:
		if not os.path.exists(path):
			raise InfraError(
				f"context {context['name']} requires {path}, which does "
				f"not exist")
	env = os.environ.copy()
	env.update(context["env"])
	log_path = os.path.join(mailbox, "log", f"context-{context['name']}.log")
	with _open_log(log_path) as log:
		boundary = {"event": "mint", "at": dt.datetime.now(
			dt.timezone.utc).isoformat(), "argv": context["command"]}
		log.write(("\n=== " + json.dumps(boundary, sort_keys=True)
		           + " ===\n").encode())
		try:
			done = subprocess.run(
				context["command"], cwd=context["cwd"], env=env,
				stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
				stderr=log, timeout=context["timeoutSeconds"],
				close_fds=True)
		except subprocess.TimeoutExpired as error:
			raise InfraError(
				f"context {context['name']} did not finish within "
				f"{context['timeoutSeconds']}s; see {log_path}") from error
		log.write(done.stdout)
	if done.returncode != 0:
		raise InfraError(
			f"context {context['name']} exited {done.returncode} without "
			f"minting anything; see {log_path}")
	try:
		minted = json.loads(done.stdout.decode("utf-8"),
		                    object_pairs_hook=_strict_object)
	except (UnicodeDecodeError, json.JSONDecodeError) as error:
		raise InfraError(
			f"context {context['name']} printed no readable JSON locator: "
			f"{error}; see {log_path}") from error
	minted = _object(minted, f"context {context['name']} output")
	for key, value in minted.items():
		if not isinstance(key, str) or not re.fullmatch(
				r"[a-zA-Z][a-zA-Z0-9_]*", key):
			raise InfraError(
				f"context {context['name']} minted an unusable field name "
				f"{key!r}")
		if not isinstance(value, (str, int, float, bool)) or value is None:
			raise InfraError(
				f"context {context['name']}.{key} must be a scalar")
	# W459 review: presence is not usability. An empty locator started
	# the service and reported the stack healthy, while `_load_state`
	# refused the very same document on the next read — a start that
	# cannot be re-read is not a start.
	if not str(minted.get(CONTEXT_NAME_FIELD, "")).strip():
		raise InfraError(
			f"context {context['name']} printed no usable "
			f"{CONTEXT_NAME_FIELD}; see {log_path}")
	record = {key: str(value) for key, value in minted.items()}
	record["mintedAt"] = dt.datetime.now(dt.timezone.utc).isoformat()
	if context["participant"]:
		record["participant"] = context["participant"]
	return record


def _render_target(mailbox, name):
	return os.path.join(_context_dir(mailbox), f"{name}.json")


def _substitute(text, minted, rendered, where, start_id=None):
	def replace(match):
		token = match.group(1)
		kind, _, rest = token.partition(".")
		if kind == "start":
			if not start_id:
				raise InfraError(
					f"{where} references {{{{start.id}}}}, which this "
					f"start has not recorded")
			return start_id
		if kind == "render":
			if rest not in rendered:
				raise InfraError(
					f"{where} references {{{{{token}}}}} before this start "
					f"rendered it")
			return rendered[rest]
		name, field = rest.split(".", 1)
		context = minted.get(name)
		if context is None or field not in context:
			raise InfraError(
				f"{where} references {{{{{token}}}}}, which this start "
				f"did not mint")
		return context[field]
	return PLACEHOLDER_RE.sub(replace, text)


def _render_files(mailbox, service, minted, rendered, start_id):
	"""Write this service's rendered files under `run/`, 0600.

	The template is the operator's and is never written to; the result
	is private runtime state that a later start overwrites."""
	directory = _context_dir(mailbox)
	_private_directory(directory)
	for entry in service["renders"]:
		target = _render_target(mailbox, entry["name"])
		# The body validated at LOAD, not a second read: re-reading
		# would reintroduce exactly the post-launch readability and
		# content race preflight just removed.
		text = _substitute(entry["body"], minted, rendered,
		                   f"render template {entry['template']}",
		                   start_id)
		# W459 review: through the SAME containment boundary as the
		# lock, the state and the logs. A private directory is not
		# enough — the same user, a faulty context command, or a race
		# can still plant a symlink here, and `O_CREAT|O_TRUNC` on a
		# pathname would then truncate a file outside the mailbox
		# entirely. `_open_owned` refuses the link, the hard link, the
		# non-regular file and the group-readable one.
		fd = _open_owned(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
		                 "rendered context file")
		with os.fdopen(fd, "w", encoding="utf-8") as handle:
			handle.write(text)
		rendered[entry["name"]] = target


def _resolved_service(service, minted, rendered, start_id):
	"""The service as it will actually be launched."""
	where = f"service {service['name']}"
	resolved = dict(service)
	resolved["command"] = [_substitute(part, minted, rendered, where,
	                                   start_id)
	                       for part in service["command"]]
	resolved["requires"] = [_substitute(part, minted, rendered, where,
	                                    start_id)
	                        for part in service["requires"]]
	resolved["env"] = {key: _substitute(value, minted, rendered, where,
	                                    start_id)
	                   for key, value in service["env"].items()}
	if service["cwd"]:
		resolved["cwd"] = _substitute(service["cwd"], minted, rendered,
		                              where, start_id)
	return resolved


def _clear_contexts(mailbox):
	directory = _context_dir(mailbox)
	try:
		names = os.listdir(directory)
	except FileNotFoundError:
		return
	for name in names:
		try:
			os.unlink(os.path.join(directory, name))
		except (FileNotFoundError, IsADirectoryError):
			pass


def _state_path(mailbox):
	return os.path.join(mailbox, "run", STATE_NAME)


def _write_state(mailbox, state_doc):
	path = _state_path(mailbox)
	temporary = os.path.join(mailbox, "run",
	                         f".{STATE_NAME}.{os.getpid()}.tmp")
	encoded = (json.dumps(state_doc, sort_keys=True, indent=2) + "\n").encode()
	fd = None
	try:
		fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
		with os.fdopen(fd, "wb") as handle:
			fd = None
			handle.write(encoded)
			handle.flush()
			os.fsync(handle.fileno())
		os.replace(temporary, path)
		os.chmod(path, 0o600)
		dir_fd = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
		try:
			os.fsync(dir_fd)
		finally:
			os.close(dir_fd)
	except OSError as error:
		if fd is not None:
			os.close(fd)
		try:
			os.unlink(temporary)
		except FileNotFoundError:
			pass
		raise InfraError(f"cannot write lifecycle state {path}: {error}") from error


def _remove_state(mailbox):
	path = _state_path(mailbox)
	try:
		os.unlink(path)
	except FileNotFoundError:
		return
	dir_fd = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
	try:
		os.fsync(dir_fd)
	finally:
		os.close(dir_fd)


def _load_state(mailbox):
	path = _state_path(mailbox)
	if not os.path.exists(path):
		return None
	info = os.lstat(path)
	if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
		raise InfraError(f"{path} is not a real state file")
	if stat.S_IMODE(info.st_mode) & 0o077:
		raise InfraError(f"{path} is not private (mode {stat.S_IMODE(info.st_mode):04o})")
	raw = _object(_read_json(path), "lifecycle state")
	_keys(raw, {"version", "mailbox", "manifestDigest", "launchOrder",
	            "startId", "contexts", "services"}, "lifecycle state")
	version = raw.get("version")
	if version not in (1, 2) or raw.get("mailbox") != mailbox:
		raise InfraError("lifecycle state has the wrong version or mailbox identity")
	if not isinstance(raw.get("manifestDigest"), str) \
			or not re.fullmatch(r"[0-9a-f]{64}", raw["manifestDigest"]):
		raise InfraError("lifecycle state has no valid manifest digest")
	order = _string_array(raw.get("launchOrder"),
	                      "lifecycle state.launchOrder", unique=True)
	services = _object(raw.get("services"), "lifecycle state.services")
	if set(order) != set(services):
		raise InfraError("lifecycle state launch order disagrees with its services")
	allowed = {"name", "pid", "startTicks", "configuredArgv", "observedArgv",
	           "argvIdentity", "log", "startedAt", "stopTimeoutSeconds"}
	for name, entry in services.items():
		if not NAME_RE.fullmatch(name):
			raise InfraError(f"lifecycle state has invalid service name {name!r}")
		entry = _object(entry, f"lifecycle state.services.{name}")
		_keys(entry, allowed, f"lifecycle state.services.{name}")
		if entry.get("name") != name:
			raise InfraError(f"lifecycle state service {name} has a disagreeing name")
		for field in ("pid", "startTicks", "stopTimeoutSeconds"):
			_positive_integer(entry.get(field),
			                  f"lifecycle state.services.{name}.{field}")
		for field in ("configuredArgv", "observedArgv"):
			if not _string_array(entry.get(field),
			                     f"lifecycle state.services.{name}.{field}"):
				raise InfraError(f"lifecycle state service {name} has empty {field}")
		_absolute(entry.get("log"), f"lifecycle state.services.{name}.log")
		_string(entry.get("startedAt"),
		        f"lifecycle state.services.{name}.startedAt")
		# W10: version 2 says, per service, whether its `observedArgv`
		# was CERTIFIED at configured readiness or merely glimpsed while
		# the launch was still arriving.
		#
		# A version-1 document has no such distinction, and that is
		# exactly its problem: the controller that wrote it recorded the
		# first readable `/proc` cmdline, which for any shebang or `env`
		# launch is a stage the exec chain was passing through. Reading
		# those entries as `final` would certify the one snapshot this
		# Work proved was never verified, so they are read as what they
		# actually are — provisional. They are never healthy, and they
		# are rolled back by `stop` on the pid, start ticks, session and
		# process group that are genuinely recorded in them.
		if version == 1:
			if "argvIdentity" in entry:
				raise InfraError(f"lifecycle state service {name} is version 1 but records an argv identity")
			entry["argvIdentity"] = "provisional"
		elif entry.get("argvIdentity") not in ("provisional", "final"):
			raise InfraError(f"lifecycle state service {name} has no valid argv identity")
	# W459: a document written before contexts existed simply has none,
	# which is the truth about it — that start minted nothing.
	minted = raw.get("contexts", {})
	if not isinstance(minted, dict):
		raise InfraError("lifecycle state.contexts must be an object")
	for name, entry in minted.items():
		if not NAME_RE.fullmatch(name):
			raise InfraError(f"lifecycle state has invalid context name {name!r}")
		entry = _object(entry, f"lifecycle state.contexts.{name}")
		if not entry.get(CONTEXT_NAME_FIELD):
			raise InfraError(
				f"lifecycle state context {name} records no "
				f"{CONTEXT_NAME_FIELD}")
	raw["contexts"] = minted
	start_id = raw.get("startId")
	if start_id is not None and (not isinstance(start_id, str)
	                             or not re.fullmatch(r"[0-9a-f]{32}",
	                                                 start_id)):
		raise InfraError("lifecycle state has an invalid start id")
	# Upgraded in memory, so any rewrite of this document — a partial
	# stop, a rollback — leaves a well-formed version 2 behind.
	raw["version"] = 2
	return raw


def _proc(pid):
	try:
		with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
			body = handle.read()
		closing = body.rfind(")")
		if closing < 0:
			return None
		fields = body[closing + 2:].split()
		state = fields[0]
		# post-comm indices: 0 state, 1 ppid, 2 pgrp, 3 session, …,
		# 19 starttime.
		pgid = int(fields[2])
		sid = int(fields[3])
		start_ticks = int(fields[19])
		with open(f"/proc/{pid}/cmdline", "rb") as handle:
			argv = [os.fsdecode(part) for part in handle.read().split(b"\0")
			        if part]
		return {"state": state, "startTicks": start_ticks, "argv": argv,
		        "pgid": pgid, "sid": sid}
	except (FileNotFoundError, ProcessLookupError, PermissionError, OSError,
	        ValueError, IndexError):
		return None


def _identity(entry):
	"""Which of the recorded facts about this service still hold.

	W10: a shebang or `/usr/bin/env` launch rewrites argv IN PLACE. The
	pid, session, process group and start ticks stay exactly the ones the
	controller created while `/proc/PID/cmdline` moves from
	`/usr/bin/env node …` to `node …` — and, for a wrapper that execs a
	different program, to an argv sharing no element with the one that
	was launched. So the argv read at launch proves OWNERSHIP and nothing
	about which program arrived.

	`argvIdentity` is that difference: `final` means the snapshot was
	captured at configured readiness, and only then does an argv change
	mean a process substituting its own identity. A `provisional` entry
	is a launch that was interrupted before readiness could certify it.
	It is owned — it must be, or nothing could roll it back — but it is
	never `owned` here, because that word is what `status` reports
	healthy and what an unqualified `stop` acts on."""
	observed = _proc(entry["pid"])
	if observed is None or observed["state"] == "Z":
		return "stopped", observed
	if observed["startTicks"] != entry["startTicks"]:
		return "pid-reused", observed
	# The default is the STRICT side. An entry assembled in memory rather
	# than loaded from lifecycle state carries no certification history,
	# and requiring its argv to match exactly is the refusal, not the
	# permission. Every entry `_load_state` returns says which it is.
	if entry.get("argvIdentity", "final") != "final":
		return "provisional", observed
	if observed["argv"] != entry["observedArgv"]:
		return "argv-mismatch", observed
	return "owned", observed


def _same_json(expected, actual):
	"""Equality in JSON's type system, not Python's.

	W482 review: Python defines `True == 1`, so a reply of
	`{"ready": 1}` satisfied `expect: {"ready": true}` and marked a
	dispatcher healthy. JSON booleans and numbers are different types
	and must not match each other. Numbers stay ONE domain — `1` and
	`1.0` are the same JSON number — because that distinction is an
	encoding detail rather than a fact about the service."""
	if isinstance(expected, bool) or isinstance(actual, bool):
		return isinstance(expected, bool) and isinstance(actual, bool) \
			and expected == actual
	if isinstance(expected, (int, float)) \
			and isinstance(actual, (int, float)):
		return expected == actual
	return type(expected) is type(actual) and expected == actual


def _control_ready(probe, readiness, deadline):
	"""Send one control line, read one reply, and match `expect`.

	Every failure here is FALSE and never an exception the controller
	reports as an inability to ask: a malformed, oversized, truncated,
	late or mismatched reply is a service that is not ready, which is
	a fact about the service rather than about the probe.

	W482 review: the whole exchange lives inside ONE absolute deadline.
	A per-operation inactivity timeout is not a bound — a peer sending
	one byte every 200 ms resets it forever, and the probe then outlives
	the service's own startup deadline because `_wait_ready` cannot
	enforce anything while it is trapped in here. Each operation gets
	what is LEFT of the budget, and nothing gets more."""
	def remaining():
		return deadline - time.monotonic()

	line = (json.dumps(readiness["request"], sort_keys=True) + "\n").encode()
	try:
		if remaining() <= 0:
			return False
		probe.settimeout(remaining())
		probe.sendall(line)
		buffer = b""
		while b"\n" not in buffer:
			left = remaining()
			if left <= 0:
				return False
			probe.settimeout(left)
			chunk = probe.recv(4096)
			if not chunk:
				# The service closed without answering: a truncated
				# reply is not a partial success.
				return False
			buffer += chunk
			if len(buffer) > CONTROL_REPLY_LIMIT:
				return False
	except (OSError, TimeoutError):
		return False
	try:
		reply = json.loads(buffer.split(b"\n", 1)[0].decode("utf-8"))
	except (UnicodeDecodeError, json.JSONDecodeError):
		return False
	if not isinstance(reply, dict):
		return False
	# TOP-LEVEL required fields, and the reply may carry any number of
	# diagnostic ones beside them.
	return all(key in reply and _same_json(value, reply[key])
	           for key, value in readiness["expect"].items())


def _ready(readiness, pid=None):
	kind = readiness["type"]
	if kind == "process":
		if pid is None:
			return False
		observed = _proc(pid)
		return observed is not None and observed["state"] != "Z"
	if kind == "unix_socket":
		# A socket PATHNAME is not readiness. The owned process can stay
		# alive while its listener goes away, and an inert socket inode
		# can sit at the same path — `stat` blesses that as healthy. So
		# prove a connection instead, exactly as the http probe beside
		# this one proves a response: a bound-but-unlistened inode
		# refuses with ECONNREFUSED, and a missing path with ENOENT.
		#
		# The connect is immediately closed. The http probe already
		# makes a real request against a live service, so a connect and
		# disconnect is the same kind of contact, not a new one.
		probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		# One budget for the whole probe — connect included — so a
		# service that answers slowly cannot borrow time from the
		# startup deadline the caller is enforcing.
		deadline = time.monotonic() + CONTROL_PROBE_SECONDS
		try:
			probe.settimeout(CONTROL_PROBE_SECONDS)
			probe.connect(readiness["path"])
			if readiness.get("request") is None:
				return True
			# W482: connected is not loaded. The service is ASKED, and
			# every way the answer can fail to arrive or fail to match
			# is "not ready yet" — the caller's retry loop and the
			# service's own startup timeout decide when that becomes a
			# failure, exactly as they already do for a socket that is
			# not there.
			return _control_ready(probe, readiness, deadline)
		except (ConnectionRefusedError, FileNotFoundError, TimeoutError):
			# The two ANSWERS a probe can legitimately get: nothing is
			# listening at the path, or there is no path. Both mean not
			# ready, and the event bridge's own stale-socket handling
			# draws the line in the same place.
			return False
		except OSError as error:
			# Anything else is not an answer about the service — it is
			# the controller unable to ask. Reporting `unhealthy` would
			# claim knowledge it does not have, which is the same defect
			# as blessing an inode: a state asserted rather than proved.
			# So it refuses by name and the operator sees why.
			raise InfraError(
				f"cannot probe readiness socket {readiness['path']}: "
				f"{error.strerror or error} (errno "
				f"{errno.errorcode.get(error.errno, error.errno)})") from None
		finally:
			probe.close()
	try:
		with urllib.request.urlopen(readiness["url"], timeout=0.25) as response:
			return response.status == readiness["expectedStatus"]
	except urllib.error.HTTPError as error:
		return error.code == readiness["expectedStatus"]
	except (urllib.error.URLError, OSError, TimeoutError):
		return False


def _wait_ready(service, pid, signals):
	deadline = time.monotonic() + service["startTimeoutSeconds"]
	stable_since = None
	while time.monotonic() < deadline:
		signals.check()
		observed = _proc(pid)
		if observed is None or observed["state"] == "Z":
			return False
		if _ready(service["readiness"], pid):
			if service["readiness"]["type"] != "process":
				return True
			if stable_since is None:
				stable_since = time.monotonic()
			if (time.monotonic() - stable_since) * 1000 >= \
					service["readiness"]["stableMilliseconds"]:
				return True
		else:
			stable_since = None
		time.sleep(0.05)
	return False


def _validate_launch(service, *, static_only=False):
	def deferred(text):
		return static_only and bool(_placeholders(text))

	executable = service["command"][0]
	if not deferred(executable) and (
			not os.path.isfile(executable)
			or not os.access(executable, os.X_OK)):
		raise InfraError(f"service {service['name']} executable is missing or not executable: {executable}")
	if service["cwd"] is not None and not deferred(service["cwd"]) \
			and not os.path.isdir(service["cwd"]):
		raise InfraError(f"service {service['name']} cwd is missing: {service['cwd']}")
	for required in service["requires"]:
		if deferred(required):
			continue
		if not os.path.exists(required):
			raise InfraError(f"service {service['name']} required path is missing: {required}")


def _open_owned(path, flags, what):
	"""Open one MAILBOX-OWNED file, refusing anything the mailbox does
	not own.

	The containment contract is the same for every private file this
	controller keeps — the lock, the lifecycle state, and each service
	log — so it is stated once here rather than re-derived at each site.
	It has four parts, and each closes a hole the others do not:

	- `O_NOFOLLOW`, because validating the descriptor afterwards cannot
	  help: the open has already followed the link, and a link to
	  another private regular file matches every remaining check.
	- `O_NONBLOCK`, because opening a FIFO waits for a peer and that
	  wait happens BEFORE any check can refuse it — the controller would
	  hang with no diagnostic instead of failing closed.
	- the descriptor's type and mode, because a directory or a
	  group-readable file is not a private file whatever its name.
	- `st_nlink`, because a HARD link defeats `O_NOFOLLOW` entirely: the
	  descriptor is a private regular file by every other measure and is
	  simply also somebody else's file. The mailbox's own files have
	  exactly one name, including across restarts.
	"""
	try:
		fd = os.open(path, flags | os.O_CLOEXEC | os.O_NOFOLLOW
		             | os.O_NONBLOCK, 0o600)
	except OSError as error:
		if error.errno in (errno.ELOOP, errno.EMLINK):
			raise InfraError(
				f"{what} {path} is a symbolic link; the mailbox owns its "
				f"lifecycle files and will not work through a link to "
				f"another file") from None
		if error.errno == errno.ENXIO:
			raise InfraError(
				f"{what} {path} is not a private regular file") from None
		raise InfraError(f"cannot open {what} {path}: {error}") from error
	try:
		flag_bits = fcntl.fcntl(fd, fcntl.F_GETFL)
		fcntl.fcntl(fd, fcntl.F_SETFL, flag_bits & ~os.O_NONBLOCK)
		info = os.fstat(fd)
		if not stat.S_ISREG(info.st_mode) or \
				stat.S_IMODE(info.st_mode) & 0o077:
			raise InfraError(f"{what} {path} is not a private regular file")
		if info.st_nlink != 1:
			raise InfraError(
				f"{what} {path} has {info.st_nlink} names; the mailbox owns "
				f"its lifecycle files and will not work through a link to "
				f"another file")
	except BaseException:
		os.close(fd)
		raise
	return fd


def _open_log(path):
	"""One mailbox-local service log, opened for append under the shared
	ownership discipline. A stale or hostile link here would send the
	launch boundary and the child's whole output into an unrelated
	file and start the service as though nothing were wrong."""
	fd = _open_owned(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT,
	                 "service log")
	return os.fdopen(fd, "ab", buffering=0)


def _wait_for_proc(pid, timeout=1.0):
	deadline = time.monotonic() + timeout
	while time.monotonic() < deadline:
		observed = _proc(pid)
		if observed is not None and observed["argv"]:
			return observed
		time.sleep(0.01)
	return None


def _group_alive(pgid):
	"""Is any member of this process group still alive?

	`kill(-pgid, 0)` asks the kernel rather than enumerating processes:
	the controller never discovers processes, it only asks about the one
	group it created."""
	try:
		os.killpg(pgid, 0)
	except ProcessLookupError:
		return False
	except PermissionError:
		# Something in the group is alive and not ours to signal. That is
		# not "stopped", and it is not ours to force either.
		return True
	return True


def _terminate(entry):
	"""Terminate the process GROUP this controller created for one
	service, or report truthfully why it did not.

	W20 R3: every service is launched with `start_new_session=True`, so
	the recorded pid is the leader of a session and process group that
	exist only because the controller made them. Signalling the leader
	alone left descendants running — the deployed ACP bridge spawns its
	agent process exactly that way — while stop removed the service from
	lifecycle state and reported success. The controller owned the whole
	group and was accounting for one process in it.

	The ownership boundary is unchanged and still fail-closed. The pidfd
	is opened FIRST and the recorded argv and start ticks rechecked
	through it, so a reused pid refuses; the group is signalled only
	after that check passes, and only when the leader really is its own
	group and session leader — which is what `start_new_session` makes,
	and what proves the group is the controller's own rather than one it
	merely joined. This never enumerates or discovers processes: it asks
	the kernel about one group id it created, and holding the pidfd is
	what keeps that id from being recycled underneath the question."""
	try:
		pidfd = os.pidfd_open(entry["pid"], 0)
	except ProcessLookupError:
		return "stopped"
	except (AttributeError, OSError):
		return "pidfd-unavailable"
	try:
		identity, observed = _identity(entry)
		if identity == "stopped":
			return "stopped"
		# W10: a PROVISIONAL entry is a launch this controller made and
		# never finished, and it is rolled back on the ownership it
		# actually has — the pid and start ticks checked just above, and
		# the session and process group checked just below. Demanding an
		# argv match as well would strand the process the controller
		# created, which is the orphan the provisional record exists to
		# prevent. A finalized entry still requires its exact recorded
		# argv, and that is where a substituted identity fails closed.
		if identity not in ("owned", "provisional"):
			return identity
		pgid = observed.get("pgid")
		own_group = (pgid == entry["pid"]
		             and observed.get("sid") == entry["pid"])
		try:
			if own_group:
				os.killpg(pgid, signal.SIGTERM)
			else:
				# Not the session the controller created — signal only
				# the recorded process. Broadening here would reach a
				# group this controller does not own, which is the one
				# thing worse than leaving a child behind.
				signal.pidfd_send_signal(pidfd, signal.SIGTERM)
		except ProcessLookupError:
			return "stopped"
		except PermissionError:
			return "not-permitted"
		watcher = select.poll()
		watcher.register(pidfd, select.POLLIN)
		deadline = time.monotonic() + entry["stopTimeoutSeconds"]
		remaining = deadline - time.monotonic()
		if not watcher.poll(max(0, remaining) * 1000):
			return "did-not-exit"
		if not own_group:
			return "stopped"
		# Reap the leader if it is this process's own child, which it is
		# during a start ROLLBACK. An unreaped exit is a zombie, and a
		# zombie is still a member of its process group — so without
		# this the group never reads as drained and a correct rollback
		# would report `group-did-not-exit` forever. On the ordinary
		# stop path the services belong to an earlier invocation and
		# this simply refuses, which is why it is guarded rather than
		# assumed.
		try:
			os.waitpid(entry["pid"], os.WNOHANG)
		except (ChildProcessError, OSError):
			pass
		# The leader is gone; the GROUP is what was owned, so wait
		# boundedly for the rest of it and stay truthful if anything
		# remains. A service is not stopped while a child it started is
		# still running.
		while _group_alive(pgid):
			if time.monotonic() >= deadline:
				return "group-did-not-exit"
			time.sleep(0.02)
		return "stopped"
	finally:
		os.close(pidfd)


def _finalize_identity(mailbox, state_doc, entry, log_path):
	"""Certify the argv of a service whose configured readiness has just
	succeeded, and mark its entry final.

	W10: readiness is the manifest's OWN declaration that this service
	finished starting. That makes it the authority boundary at which the
	observed argv stops being a glimpse of an exec chain in motion and
	becomes the identity every later `status` and `stop` must match
	exactly.

	The first attempt at this Work drew the boundary with a fixed 250 ms
	quiet interval instead. The live smoke disproved it: a launcher
	stayed in its own argv longer than the interval while the kernel and
	runtime loaded the next executable, so the controller certified the
	launcher and reported the very `argv-mismatch` this Work exists to
	remove. Waiting longer would have moved that race, not closed it —
	no interval can know that an exec chain is finished. Readiness
	already carries that knowledge, declared per service by the operator,
	so there is no second competing timer here.

	Nothing below reads what the argv CONTAINS. No interpreter, launcher,
	wrapper, Node path, or command shape is named anywhere."""
	observed = _proc(entry["pid"])
	if observed is None or observed["state"] == "Z" or not observed["argv"]:
		raise InfraError(f"service {entry['name']} exited as its identity was recorded; see {log_path}")
	if observed["startTicks"] != entry["startTicks"]:
		raise InfraError(f"service {entry['name']} pid {entry['pid']} was reused before its identity could be recorded; see {log_path}")
	# One atomic write moves the entry from provisional to final, so a
	# controller interrupted here leaves a provisional entry with its
	# ownership intact rather than a half-certified one.
	entry["observedArgv"] = observed["argv"]
	entry["argvIdentity"] = "final"
	_write_state(mailbox, state_doc)


def _new_start_id():
	"""This start's identity. Random rather than a counter: two mailboxes
	must not collide, and a controller killed between starts must not
	reuse the identity of the one before it."""
	return uuid.uuid4().hex


def _empty_state(mailbox, manifest):
	# W459: `contexts` records what THIS start minted. It is written
	# before the services that reference it launch, so a controller
	# killed mid-startup leaves the locators it created behind as
	# evidence rather than as an untracked thread nobody can name.
	return {"version": 2, "mailbox": mailbox,
	        "manifestDigest": manifest["digest"], "launchOrder": [],
	        "startId": _new_start_id(), "contexts": {}, "services": {}}


def _report(command, healthy, services, **extra):
	payload = {"command": command, "healthy": healthy, "services": services}
	payload.update(extra)
	print(json.dumps(payload, sort_keys=True, indent=2))


def _start_guarded(mailbox, manifest, signals):
	state_doc = _load_state(mailbox)
	if state_doc is not None:
		healthy, rows = status_rows(mailbox, manifest, state_doc)
		if healthy:
			_report("start", True, rows, already_running=True)
			return 0
		_report("start", False, rows, error="existing lifecycle state is not a complete healthy configured set; refusing to adopt, replace, or kill it")
		return 2
	for name in manifest["order"]:
		service = manifest["services"][name]
		# W459: pre-flight can only judge what this start has not
		# minted yet. A path naming a context or a render is checked
		# for real in the launch loop, once it HAS a value; checking
		# the literal `{{…}}` here would refuse every manifest that
		# uses one.
		_validate_launch(service, static_only=True)
		if service["readiness"]["type"] != "process" \
				and _ready(service["readiness"]):
			raise InfraError(f"service {name} readiness is already satisfied without owned state; refusing to adopt it")
	state_doc = _empty_state(mailbox, manifest)
	_write_state(mailbox, state_doc)
	started = []
	# W459: nothing from a previous start is carried in. The map begins
	# EMPTY on every start, and the files a previous start rendered are
	# cleared before anything can read one by accident.
	minted = {}
	rendered = {}
	_clear_contexts(mailbox)
	try:
		pending_contexts = list(manifest["contextOrder"])
		for name in manifest["order"]:
			signals.check()
			# A context is minted once every service it waits on is
			# ready — which is why it happens HERE rather than before
			# the loop: `--start-thread` needs the app-server up.
			for context_name in list(pending_contexts):
				context = manifest["contexts"][context_name]
				if any(dependency not in started
				       for dependency in context["after"]):
					continue
				minted[context_name] = _mint_context(mailbox, context,
				                                     signals)
				pending_contexts.remove(context_name)
				state_doc["contexts"] = minted
				_write_state(mailbox, state_doc)
			# Rendered first: a service may point at the file this
			# start writes, so the file has to exist before its argv
			# can name it.
			if manifest["services"][name]["renders"]:
				_render_files(mailbox, manifest["services"][name],
				              minted, rendered, state_doc["startId"])
			service = _resolved_service(manifest["services"][name],
			                            minted, rendered,
			                            state_doc["startId"])
			_validate_launch(service)
			log_path = os.path.join(mailbox, "log", f"{name}.log")
			with _open_log(log_path) as log:
				boundary = {"event": "launch", "at": dt.datetime.now(
					dt.timezone.utc).isoformat(), "argv": service["command"]}
				log.write(("\n=== " + json.dumps(boundary, sort_keys=True)
				           + " ===\n").encode())
				env = os.environ.copy()
				env.update(service["env"])
				process = subprocess.Popen(
					service["command"], cwd=service["cwd"], env=env,
					stdin=subprocess.DEVNULL, stdout=log,
					stderr=subprocess.STDOUT, start_new_session=True,
					close_fds=True)
			observed = _wait_for_proc(process.pid)
			if observed is None:
				try:
					process.terminate()
					process.wait(timeout=1)
				except (ProcessLookupError, subprocess.SubprocessError):
					pass
				raise InfraError(f"service {name} exited before its identity could be recorded; see {log_path}")
			entry = {
				"name": name, "pid": process.pid,
				"startTicks": observed["startTicks"],
				"configuredArgv": service["command"],
				"observedArgv": observed["argv"],
				"argvIdentity": "provisional", "log": log_path,
				"startedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
				"stopTimeoutSeconds": service["stopTimeoutSeconds"],
			}
			state_doc["launchOrder"].append(name)
			state_doc["services"][name] = entry
			started.append(name)
			# Recorded BEFORE readiness, and deliberately. The argv in it
			# is provisional, but the pid and start ticks in it are
			# already the whole ownership record — so a controller killed
			# anywhere in the interval below leaves behind a service that
			# `stop` can still prove it owns and roll back, rather than an
			# orphan nothing accounts for.
			_write_state(mailbox, state_doc)
			signals.check()
			if not _wait_ready(service, process.pid, signals):
				raise InfraError(f"service {name} failed readiness within {service['startTimeoutSeconds']}s; see {log_path}")
			_finalize_identity(mailbox, state_doc, entry, log_path)
			signals.check()
		for context_name in pending_contexts:
			minted[context_name] = _mint_context(
				mailbox, manifest["contexts"][context_name], signals)
			state_doc["contexts"] = minted
			_write_state(mailbox, state_doc)
		signals.check()
	except (InfraError, OSError, subprocess.SubprocessError) as error:
		rollback_errors = []
		for name in reversed(started):
			result = _terminate(state_doc["services"][name])
			if result == "stopped":
				state_doc["launchOrder"].remove(name)
				del state_doc["services"][name]
			else:
				rollback_errors.append(f"{name}: {result}")
		if state_doc["services"]:
			_write_state(mailbox, state_doc)
		else:
			# Nothing of this start survives, including the files it
			# rendered: leaving them would let the NEXT start read a
			# locator this one already abandoned.
			_clear_contexts(mailbox)
			_remove_state(mailbox)
		suffix = "" if not rollback_errors else "; rollback refused: " \
			+ ", ".join(rollback_errors)
		raise InfraError(f"startup failed: {error}{suffix}") from error
	healthy, rows = status_rows(mailbox, manifest, state_doc)
	_report("start", healthy, rows, already_running=False)
	return 0 if healthy else 2


def start(mailbox, manifest):
	with StartupSignalGuard() as signals:
		return _start_guarded(mailbox, manifest, signals)


def _expected_argv(mailbox, service, state_doc):
	"""The argv this manifest would produce given the recorded start.

	A manifest with no placeholders answers exactly what it always
	did; one with placeholders is resolved against the contexts the
	state says were minted, so `status` compares like with like. A
	placeholder the state cannot resolve leaves the raw text, which
	CANNOT match a launched argv — the honest answer for a service
	whose configuration no longer describes what is running."""
	minted = (state_doc or {}).get("contexts", {})
	start_id = (state_doc or {}).get("startId")
	rendered = {entry["name"]: _render_target(mailbox, entry["name"])
	            for entry in service["renders"]}
	out = []
	for part in service["command"]:
		try:
			out.append(_substitute(part, minted, rendered,
			                       f"service {service['name']}",
			                       start_id))
		except InfraError:
			out.append(part)
	return out


def status_rows(mailbox, manifest, state_doc):
	manifest_match = state_doc is not None \
		and state_doc["manifestDigest"] == manifest["digest"]
	rows = []
	state_services = {} if state_doc is None else state_doc["services"]
	for name in manifest["order"]:
		service = manifest["services"][name]
		entry = state_services.get(name)
		log = os.path.join(mailbox, "log", f"{name}.log")
		if entry is None:
			rows.append({"name": name, "pid": None, "state": "stopped",
			             "healthy": False, "log": log})
			continue
		identity, _observed = _identity(entry)
		# W459: the manifest's command may carry `{{context…}}`
		# placeholders, so it is compared against the argv resolved
		# with the contexts THIS start minted — which the state
		# records. The check is unchanged in what it protects: an
		# operator editing the manifest under a running set still
		# reads as `configuration-changed`, and so does a service now
		# pointed at a locator this start did not mint.
		expected = _expected_argv(mailbox, service, state_doc)
		if not manifest_match or entry["configuredArgv"] != expected:
			state = "configuration-changed"
		elif identity != "owned":
			state = identity
		elif not _ready(service["readiness"], entry["pid"]):
			state = "unhealthy"
		else:
			state = "healthy"
		rows.append({"name": name, "pid": entry["pid"], "state": state,
		             "healthy": state == "healthy", "log": entry["log"]})
	for name in sorted(set(state_services) - set(manifest["services"])):
		entry = state_services[name]
		identity, _observed = _identity(entry)
		rows.append({"name": name, "pid": entry["pid"],
		             "state": "state-only" if identity == "owned" else identity,
		             "healthy": False, "log": entry["log"]})
	healthy = manifest_match and len(rows) == len(manifest["services"]) \
		and all(row["healthy"] for row in rows)
	return healthy, rows


def status_command(mailbox, manifest):
	state_doc = _load_state(mailbox)
	healthy, rows = status_rows(mailbox, manifest, state_doc)
	_report("status", healthy, rows,
	        state="running" if healthy else
	        ("stopped" if state_doc is None else "partial-or-stale"))
	return 0 if healthy else 1


def stop(mailbox, manifest=None):
	state_doc = _load_state(mailbox)
	if state_doc is None:
		if manifest is None:
			manifest = load_manifest(mailbox)
		rows = [{"name": name, "pid": None, "state": "stopped",
		         "healthy": False,
		         "log": os.path.join(mailbox, "log", f"{name}.log")}
		        for name in manifest["order"]]
		_report("stop", True, rows, already_stopped=True)
		return 0
	rows = []
	failures = []
	for name in reversed(list(state_doc["launchOrder"])):
		entry = state_doc["services"][name]
		result = _terminate(entry)
		rows.append({"name": name, "pid": entry["pid"], "state": result,
		             "healthy": False, "log": entry["log"]})
		if result == "stopped":
			state_doc["launchOrder"].remove(name)
			del state_doc["services"][name]
			if state_doc["services"]:
				_write_state(mailbox, state_doc)
			else:
				_remove_state(mailbox)
		else:
			failures.append(f"{name}: {result}")
	if state_doc["services"]:
		_write_state(mailbox, state_doc)
	_report("stop", not failures, rows,
	        **({} if not failures else {"error": "refused or incomplete stops: "
	                                      + ", ".join(failures)}))
	return 0 if not failures else 2


def run(argv=None):
	parser = argparse.ArgumentParser(
		description="start, stop, or inspect one mailbox-owned v11 backend set")
	parser.add_argument("command", choices=("start", "stop", "status"))
	parser.add_argument("mailbox")
	options = parser.parse_args(argv)
	mailbox = os.path.realpath(os.path.abspath(options.mailbox))
	if not os.path.isdir(mailbox):
		raise InfraError(f"MAILBOX is not a directory: {mailbox}")
	with MailboxLock(mailbox):
		if options.command == "stop":
			state_doc = _load_state(mailbox)
			manifest = None if state_doc is not None else load_manifest(mailbox)
			return stop(mailbox, manifest)
		manifest = load_manifest(mailbox)
		if options.command == "start":
			return start(mailbox, manifest)
		return status_command(mailbox, manifest)


def main():
	try:
		return run()
	except InfraError as error:
		print(json.dumps({"error": str(error)}), file=sys.stderr)
		return 2


if __name__ == "__main__":
	raise SystemExit(main())
