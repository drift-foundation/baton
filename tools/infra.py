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
		_keys(raw, {"type", "path"}, where)
		return {"type": kind, "path": _absolute(raw.get("path"),
		                                             f"{where}.path")}
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
	            "services"}, "manifest")
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
	allowed = {"name", "command", "after", "cwd", "env", "requires",
	           "participant", "readiness", "startTimeoutSeconds",
	           "stopTimeoutSeconds"}
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
	return {
		"path": path,
		"digest": hashlib.sha256(encoded).hexdigest(),
		"startTimeoutSeconds": start_timeout,
		"stopTimeoutSeconds": stop_timeout,
		"services": services,
		"order": order,
	}


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
	            "services"}, "lifecycle state")
	if raw.get("version") != 1 or raw.get("mailbox") != mailbox:
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
	           "log", "startedAt", "stopTimeoutSeconds"}
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
	observed = _proc(entry["pid"])
	if observed is None or observed["state"] == "Z":
		return "stopped", observed
	if observed["startTicks"] != entry["startTicks"]:
		return "pid-reused", observed
	if observed["argv"] != entry["observedArgv"]:
		return "argv-mismatch", observed
	return "owned", observed


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
		try:
			probe.settimeout(0.25)
			probe.connect(readiness["path"])
			return True
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


def _validate_launch(service):
	executable = service["command"][0]
	if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
		raise InfraError(f"service {service['name']} executable is missing or not executable: {executable}")
	if service["cwd"] is not None and not os.path.isdir(service["cwd"]):
		raise InfraError(f"service {service['name']} cwd is missing: {service['cwd']}")
	for required in service["requires"]:
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
		if identity != "owned":
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


def _empty_state(mailbox, manifest):
	return {"version": 1, "mailbox": mailbox,
	        "manifestDigest": manifest["digest"], "launchOrder": [],
	        "services": {}}


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
		_validate_launch(service)
		if service["readiness"]["type"] != "process" \
				and _ready(service["readiness"]):
			raise InfraError(f"service {name} readiness is already satisfied without owned state; refusing to adopt it")
	state_doc = _empty_state(mailbox, manifest)
	_write_state(mailbox, state_doc)
	started = []
	try:
		for name in manifest["order"]:
			signals.check()
			service = manifest["services"][name]
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
				"observedArgv": observed["argv"], "log": log_path,
				"startedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
				"stopTimeoutSeconds": service["stopTimeoutSeconds"],
			}
			state_doc["launchOrder"].append(name)
			state_doc["services"][name] = entry
			started.append(name)
			_write_state(mailbox, state_doc)
			signals.check()
			if not _wait_ready(service, process.pid, signals):
				raise InfraError(f"service {name} failed readiness within {service['startTimeoutSeconds']}s; see {log_path}")
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
		if not manifest_match or entry["configuredArgv"] != service["command"]:
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
