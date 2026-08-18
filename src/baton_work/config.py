"""The v11 `baton.json` schema and loader — correction step C1. PURE.

This module reads and validates; it never opens the authority and never
writes. Everything the instance IS gets declared here once — identity,
topology, responsibility — and validated before any other code runs, because
topology discovered piecemeal and identity by assertion are the two defects
the configuration boundary exists to end (ruling, 2026-08-14).

THE IDENTITY LIVES IN THE DOCUMENT. `instance.authority_uuid` is the stable
mailbox identity and `work.sqlite3` is its fixed sibling — no separate
handshake file exists (WORK.json is superseded by ruling). Copying
`baton.json` copies the mailbox's identity on purpose; a genuinely new
mailbox gets a new UUID before generation 1 is accepted. C2 owns the
authority-side half of that validation; C1 owns the document.

STRICT EVERYWHERE: duplicate keys refused at parse, unknown fields refused
at every level, every handle measured against the 6/6 display-cell grammar,
every reference resolved (a route's role must exist, a handler must hold the
role, a kind's route must exist) — a configuration error is refused at load
with the field named, never discovered at tag time.
"""

from __future__ import annotations

import os

import json
import re

from baton_work.authority import (
	PROTOCOL_VERSION,
	WorkError,
	validate_handle,
)

CONFIG_VERSION = 1
DATABASE_NAME = "work.sqlite3"
CAPABILITIES = ("config",)

_UUID = re.compile(r"\A[0-9a-f]{32}\Z")


def _exact_int(value, what: str) -> int:
	"""An integer that is actually an integer: bool is a subclass of int and
	1.0 == 1, so equality alone admits `true` and floats — the reviewer
	reproduced both."""
	if type(value) is not int:
		raise WorkError(f"{what} must be an integer, not "
		                f"{type(value).__name__}")
	return value


def _string_list(value, what: str, *, nonempty: bool = False) -> list[str]:
	"""A list of unique strings. Non-string members refuse HERE, with the
	field named, so no downstream membership test ever meets a raw
	TypeError."""
	if not isinstance(value, list):
		raise WorkError(f"{what} must be a list")
	for item in value:
		if not isinstance(item, str):
			raise WorkError(f"{what} contains {item!r}, which is not a "
			                f"string")
	if len(set(value)) != len(value):
		duplicates = sorted({item for item in value
		                     if value.count(item) > 1})
		raise WorkError(f"{what} lists {duplicates} more than once; a "
		                f"repeated entry is a claim nothing distinguishes")
	if nonempty and not value:
		raise WorkError(f"{what} must not be empty")
	return value


def _no_duplicates(pairs):
	seen = {}
	for key, value in pairs:
		if key in seen:
			raise WorkError(f"duplicate object key {key!r}; a configuration "
			                f"that says a thing twice is not a configuration")
		seen[key] = value
	return seen


_ROOT_ID = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")


def validate_root_id(root: str, what: str = "root") -> str:
	"""WS-6: configured root ids keep the proven protocol-10 grammar —
	up to 64 bytes of dotted lowercase/underscore segments — NOT the
	v11 team/member handle grammar."""
	if not isinstance(root, str) or not root or \
			len(root.encode("utf-8")) > 64 or not _ROOT_ID.match(root):
		raise WorkError(
			f"{what} id {root!r} is not a valid root identifier: up to "
			f"64 bytes of dotted lowercase/underscore segments "
			f"(protocol-10 root grammar)")
	return root


def _strict_object(value, what: str, allowed: tuple[str, ...],
                   required: tuple[str, ...]) -> dict:
	if not isinstance(value, dict):
		raise WorkError(f"{what} must be a JSON object")
	unknown = set(value) - set(allowed)
	if unknown:
		raise WorkError(f"{what} carries unknown fields {sorted(unknown)}; "
		                f"a configuration is not a place to put things "
		                f"nothing checks")
	missing = [name for name in required if name not in value]
	if missing:
		raise WorkError(f"{what} is missing {missing}")
	return value


def _display(value, what: str) -> str:
	if not isinstance(value, str) or not value.strip():
		raise WorkError(f"{what} needs a non-empty display name")
	return value


def loads(raw: str) -> dict:
	"""Parse and validate a v11 configuration document from its bytes."""
	try:
		document = json.loads(raw, object_pairs_hook=_no_duplicates)
	except WorkError:
		raise
	except ValueError as broken:
		raise WorkError(f"configuration is not valid JSON: {broken}") from None

	_strict_object(document, "the configuration",
	               ("config_version", "protocol_version", "generation",
	                "instance", "teams", "roots"),
	               ("config_version", "protocol_version", "generation",
	                "instance", "teams"))
	if _exact_int(document["config_version"], "config_version") != \
			CONFIG_VERSION:
		raise WorkError(f"config_version {document['config_version']!r} is "
		                f"not {CONFIG_VERSION}; this build does not guess "
		                f"across config versions")
	if _exact_int(document["protocol_version"],
	              "protocol_version") != PROTOCOL_VERSION:
		raise WorkError(
			f"configuration declares protocol "
			f"{document['protocol_version']!r}; this build speaks protocol "
			f"{PROTOCOL_VERSION}. The path never substitutes for this check.")
	generation = _exact_int(document["generation"], "generation")
	if generation < 1:
		raise WorkError(f"generation {generation!r} is not a positive integer")

	instance = _strict_object(document["instance"], "instance",
	                          ("name", "authority_uuid", "database"),
	                          ("name", "authority_uuid", "database"))
	_display(instance["name"], "instance")
	if not isinstance(instance["authority_uuid"], str) or \
			not _UUID.match(instance["authority_uuid"]):
		raise WorkError("instance.authority_uuid must be 32 lowercase hex "
		                "characters; it is the mailbox's stable identity")
	if instance["database"] != DATABASE_NAME:
		raise WorkError(
			f"instance.database is {instance['database']!r}; the authority "
			f"is the fixed sibling {DATABASE_NAME!r} and the field exists to "
			f"say so, not to relocate it")

	teams = document["teams"]
	if not isinstance(teams, dict):
		raise WorkError("teams must be a JSON object")
	if not teams:
		raise WorkError("teams must not be empty; an instance with nobody "
		                "in it is a mistake, not a bootstrap")

	# WS-6: the portable root catalog — optional, strict, v10 grammar.
	roots = document.get("roots", {})
	if not isinstance(roots, dict):
		raise WorkError("roots must be a JSON object of root id to entry")
	for root_id, entry in roots.items():
		validate_root_id(root_id)
		named = f"root {root_id!r}"
		# W4: baton.json is the SINGLE explicit root config — every
		# root declares its absolute base here; no machine-local
		# resolver file and no filesystem inference. Validation is
		# pure syntax; existence is checked at use time.
		_strict_object(entry, named, ("display", "base"),
		               ("display", "base"))
		_display(entry["display"], named)
		base = entry["base"]
		if not isinstance(base, str) or not base.strip() or \
				not os.path.isabs(base):
			raise WorkError(
				f"{named} must declare an explicit absolute base "
				f"path; got {base!r} — a client opened with "
				f"baton.json knows every repository base explicitly")
	for team_handle, team in teams.items():
		validate_handle(team_handle, "team")
		where = f"team {team_handle!r}"
		_strict_object(team, where,
		               ("display", "participants", "roles", "routes", "kinds"),
		               ("display", "participants", "roles", "routes", "kinds"))
		_display(team["display"], where)

		roles = team["roles"]
		if not isinstance(roles, dict):
			raise WorkError(f"{where} roles must be an object")
		for role_handle, role in roles.items():
			validate_handle(role_handle, "role")
			# W101 (superseding its own optional-instructions boundary):
			# EVERY declared role carries durable operating
			# instructions. Optional instructions made an uninstructed
			# role look like a complete deployment while any agent
			# launched into it fell back to whatever prompt an operator
			# happened to remember — the one-off prompt this Work exists
			# to retire. A deployment with an uninstructed role is
			# incomplete and refuses here, at acceptance, rather than at
			# the launch that needed the text.
			#
			# Deliberately role-GENERIC: this requires instructions on
			# every declared role and never names a particular role
			# handle. Which roles a deployment declares, and what their
			# texts must say, is that deployment's ruling and not the
			# protocol's.
			_strict_object(role, f"{where} role {role_handle!r}",
			               ("display", "instructions"),
			               ("display", "instructions"))
			_display(role["display"], f"{where} role {role_handle!r}")
			if not isinstance(role["instructions"], str) or \
					not role["instructions"].strip():
				raise WorkError(
					f"{where} role {role_handle!r} instructions must be a "
					f"non-empty string: every role carries the durable "
					f"operating instructions an agent launched into it "
					f"receives")

		participants = team["participants"]
		if not isinstance(participants, dict) or not participants:
			raise WorkError(f"{where} needs at least one participant")
		for member_handle, member in participants.items():
			validate_handle(member_handle, "member")
			who = f"participant {team_handle}.{member_handle}"
			_strict_object(member, who,
			               ("display", "roles", "capabilities"),
			               ("display", "roles"))
			_display(member["display"], who)
			held = _string_list(member["roles"], f"{who} roles")
			for role_handle in held:
				if role_handle not in roles:
					raise WorkError(f"{who} holds role {role_handle!r}, "
					                f"which {where} does not declare")
			capabilities = _string_list(
				member.get("capabilities", []), f"{who} capabilities")
			for capability in capabilities:
				if capability not in CAPABILITIES:
					raise WorkError(
						f"{who} claims capability {capability!r}; this build "
						f"knows {list(CAPABILITIES)}")

		routes = team["routes"]
		if not isinstance(routes, dict):
			raise WorkError(f"{where} routes must be an object")
		for route_handle, route in routes.items():
			validate_handle(route_handle, "route")
			named = f"{where} route {route_handle!r}"
			_strict_object(route, named, ("role", "handlers"),
			               ("role", "handlers"))
			if not isinstance(route["role"], str) or \
					route["role"] not in roles:
				raise WorkError(f"{named} names role {route['role']!r}, "
				                f"which {where} does not declare")
			handlers = _string_list(route["handlers"], f"{named} handlers")
			if not handlers:
				raise WorkError(f"{named} needs at least one handler; a "
				                f"route that resolves to nobody is refused "
				                f"at configuration time, not discovered at "
				                f"tag time")
			for handler in handlers:
				if handler not in participants:
					raise WorkError(f"{named} handler {handler!r} is not a "
					                f"participant of {where}")
				if route["role"] not in participants[handler]["roles"]:
					raise WorkError(
						f"{named} handler {handler!r} does not hold role "
						f"{route['role']!r}; responsibility must be held, "
						f"not merely assigned")

		kinds = team["kinds"]
		if not isinstance(kinds, dict):
			raise WorkError(f"{where} kinds must be an object")
		for kind_handle, kind in kinds.items():
			validate_handle(kind_handle, "kind")
			named = f"{where} kind {kind_handle!r}"
			# W230: one VISIBLE kind may offer more than one route. The
			# `route` stays the deterministic default — omitted selection
			# always resolves to it — and `alternates` names the routes
			# an operator may select explicitly. Baton never fails over,
			# races them, or shows every candidate on a Work row; the
			# choice is a deliberate per-Work act or it does not happen.
			_strict_object(kind, named, ("display", "route", "alternates"),
			               ("display", "route"))
			_display(kind["display"], named)
			if not isinstance(kind["route"], str) or \
					kind["route"] not in routes:
				raise WorkError(f"{named} resolves through route "
				                f"{kind['route']!r}, which {where} does not "
				                f"declare")
			alternates = kind.get("alternates")
			if alternates is not None:
				alternates = _string_list(alternates, f"{named} alternates")
				default_role = routes[kind["route"]]["role"]
				for alternate in alternates:
					if alternate not in routes:
						raise WorkError(
							f"{named} names alternate route "
							f"{alternate!r}, which {where} does not declare")
					if alternate == kind["route"]:
						raise WorkError(
							f"{named} lists its own default route "
							f"{alternate!r} as an alternate; the default is "
							f"already selectable")
					# The endpoint's MEANING must not change with the
					# route. An alternate carrying a different role would
					# make `baton.impl` mean implementation or review
					# depending on a per-Work choice, which is exactly
					# what the visible endpoint exists to prevent.
					if routes[alternate]["role"] != default_role:
						raise WorkError(
							f"{named} alternate route {alternate!r} carries "
							f"role {routes[alternate]['role']!r}, not the "
							f"endpoint's {default_role!r}; an alternate "
							f"changes WHO handles the Work, never what the "
							f"endpoint means")
	return document


def load(path: str) -> dict:
	"""Read one configuration file. Pure: one open, one read, no writes."""
	try:
		with open(path, "r", encoding="utf-8") as handle:
			raw = handle.read()
	except FileNotFoundError:
		raise WorkError(f"{path} does not exist; a v11 instance is its "
		                f"configuration, and there is nothing to open "
		                f"without one") from None
	except UnicodeDecodeError:
		raise WorkError(f"{path} is not valid UTF-8") from None
	try:
		return loads(raw)
	except WorkError as refusal:
		raise WorkError(f"{path}: {refusal}") from None


def participants(document: dict) -> list[str]:
	"""Every configured participant as `team.member`, sorted. Pure helper
	for the surfaces that resolve `--participant`."""
	out = []
	for team_handle, team in document["teams"].items():
		for member_handle in team["participants"]:
			out.append(f"{team_handle}.{member_handle}")
	return sorted(out)


def participant_instructions(document: dict, participant: str,
                             role: str) -> dict:
	"""Resolve one participant's durable operating instructions.

	W101 (superseding its own inference rule): the role is ALWAYS
	explicit, even when the participant holds exactly one. Inferring it
	meant that giving a participant a second role later would silently
	change the persona of every session launched for them — a
	deployment edit quietly rewriting who an agent is. Naming the role
	makes the participant, the role, and therefore the scope of the
	session auditable deployment inputs.

	Instructions are owned by the ROLE and inherited by every member
	launched in it. They are never copied into member entries, so
	correcting a role's text corrects every session started from it.
	"""
	team_handle, dot, member_handle = str(participant).partition(".")
	team = document.get("teams", {}).get(team_handle)
	member = team.get("participants", {}).get(member_handle) if dot and team else None
	if member is None:
		raise WorkError(f"participant {participant!r} is not in the accepted configuration")
	roles = team["roles"]
	held = member["roles"]
	if not isinstance(role, str) or not role.strip():
		raise WorkError(
			f"launching {participant} needs an explicit role=; a "
			f"participant holding one role today may hold two tomorrow, "
			f"and the session's persona must not change on that edit")
	if role not in held:
		raise WorkError(f"participant {participant} does not hold role {role!r}; select one of {sorted(held)}")
	selected = role
	entry = roles[selected]
	if "instructions" not in entry:
		raise WorkError(f"role {team_handle}.{selected} has no configured instructions")
	return {"participant": participant, "role": selected,
	        "instructions": entry["instructions"],
	        "configuration_generation": document["generation"]}
