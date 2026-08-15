"""Configuration ↔ authority binding — correction step C2.

Three acts and nothing else lives here:

`init_from_config` — generation-1 bootstrap, CRASH-SAFE: the database is
built complete in a uniquely-named temp sibling and published by one atomic
rename; a crash at any point leaves either no `work.sqlite3` (retry works) or
a whole one (retry refuses), never a half-initialized authority anyone can
open. The uuid comes FROM the config: identity lives in `baton.json` by
ruling, and this merely binds it.

`open_bound` — the ordinary open. It validates the triangle directly (no
WORK.json exists): the file's digest equals the accepted digest, the file's
uuid equals the authority's, the generations agree. An edited config is a
proposal awaiting acceptance and is refused in those words.

`accept_config` — the bounded acceptance path, the ONE exception to the
digest refusal: it opens the authority by its ACCEPTED state and reads the
proposal separately, requiring `generation == accepted + 1` declared in the
proposal itself. One audited transaction; only a participant holding the
`config` capability IN THE CURRENTLY ACCEPTED generation may accept, so a
proposal cannot authorize its own acceptor; a proposal that would strand
open Work or pending obligations refuses and names them; retired or removed
identities keep their meaning and are never silently reused.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

from baton_work.authority import (Authority, WorkError,
                                  validate_op_id)
from baton_work import config as cfg

DATABASE = cfg.DATABASE_NAME


def _digest(raw: bytes) -> str:
	return hashlib.sha256(raw).hexdigest()


def _read_config(config_path: str) -> tuple[dict, str]:
	try:
		with open(config_path, "rb") as handle:
			raw = handle.read()
	except FileNotFoundError:
		raise WorkError(f"{config_path} does not exist; a v11 instance is "
		                f"its configuration") from None
	try:
		document = cfg.loads(raw.decode("utf-8"))
	except UnicodeDecodeError:
		raise WorkError(f"{config_path} is not valid UTF-8") from None
	except WorkError as refusal:
		raise WorkError(f"{config_path}: {refusal}") from None
	return document, _digest(raw)


def _database_path(config_path: str) -> str:
	return os.path.join(os.path.dirname(os.path.abspath(config_path)),
	                    DATABASE)


def _project(conn, document: dict) -> None:
	"""Write the topology tables as the projection of one accepted document.

	Additive-and-mark, never delete: rows for identities absent from the
	document get `removed=1` (kinds: `retired=1`), because history needs the
	name to stay taken and old events to keep meaning."""
	teams = document["teams"]
	conn.execute("UPDATE teams SET removed=1")
	conn.execute("UPDATE members SET removed=1")
	conn.execute("UPDATE roles SET removed=1")
	conn.execute("UPDATE routes SET removed=1")
	conn.execute("UPDATE kinds SET retired=1")
	conn.execute("UPDATE roots SET removed=1")
	for root_id, entry in document.get("roots", {}).items():
		conn.execute(
			"INSERT INTO roots (root, display, removed) VALUES (?, ?, 0) "
			"ON CONFLICT (root) DO UPDATE SET display=excluded.display, "
			"removed=0", (root_id, entry["display"]))
	conn.execute("DELETE FROM route_handlers")
	conn.execute("DELETE FROM member_roles")
	conn.execute("DELETE FROM member_capabilities")
	for team_handle, team in teams.items():
		conn.execute(
			"INSERT INTO teams (handle, display, removed) VALUES (?, ?, 0) "
			"ON CONFLICT (handle) DO UPDATE SET display=excluded.display, "
			"removed=0", (team_handle, team["display"]))
		for member_handle, member in team["participants"].items():
			conn.execute(
				"INSERT INTO members (team, handle, display, removed) "
				"VALUES (?, ?, ?, 0) ON CONFLICT (team, handle) DO UPDATE "
				"SET display=excluded.display, removed=0",
				(team_handle, member_handle, member["display"]))
			for role in member["roles"]:
				conn.execute(
					"INSERT INTO member_roles (team, member, role) "
					"VALUES (?, ?, ?)", (team_handle, member_handle, role))
			for capability in member.get("capabilities", []):
				conn.execute(
					"INSERT INTO member_capabilities (team, member, "
					"capability) VALUES (?, ?, ?)",
					(team_handle, member_handle, capability))
		for role_handle, role in team["roles"].items():
			conn.execute(
				"INSERT INTO roles (team, handle, display, removed) "
				"VALUES (?, ?, ?, 0) ON CONFLICT (team, handle) DO UPDATE "
				"SET display=excluded.display, removed=0",
				(team_handle, role_handle, role["display"]))
		for route_handle, route in team["routes"].items():
			conn.execute(
				"INSERT INTO routes (team, handle, role, removed) "
				"VALUES (?, ?, ?, 0) ON CONFLICT (team, handle) DO UPDATE "
				"SET role=excluded.role, removed=0",
				(team_handle, route_handle, route["role"]))
			for handler in route["handlers"]:
				conn.execute(
					"INSERT INTO route_handlers (team, route, member) "
					"VALUES (?, ?, ?)", (team_handle, route_handle, handler))
		for kind_handle, kind in team["kinds"].items():
			conn.execute(
				"INSERT INTO kinds (team, handle, display, route, retired) "
				"VALUES (?, ?, ?, ?, 0) ON CONFLICT (team, handle) DO UPDATE "
				"SET display=excluded.display, route=excluded.route, "
				"retired=0",
				(team_handle, kind_handle, kind["display"], kind["route"]))


def _parse_config_refs(refs, catalog, *, allow_dossier: bool) -> list:
	"""WS-6 R89: the configuration family uses the ONE typed reference
	vocabulary — same grammar, same normalizer, same containment. Fresh
	generation-one activation refuses the dossier form (no bound Work
	can exist yet); regen accepts it, with the store-touching peek and
	revision pinning deferred to the identity-gated committing path.
	Independent references land on the catalog THIS acceptance
	proposes."""
	from baton_work.transitions import _parse_ref_tokens
	parsed = _parse_ref_tokens(refs)
	for ref in parsed:
		if ref["kind"] == "dossier":
			if not allow_dossier:
				raise WorkError(
					f"{ref['work']}: generation one has no bound work "
					f"to cite; a fresh activation carries independent "
					f"ROOT_ID:path references only")
		elif ref["root"] not in catalog:
			raise WorkError(
				f"root {ref['root']!r} is not in the root catalog this "
				f"acceptance proposes; an independent reference lands "
				f"on the accepted catalog")
	return parsed


def _op_tuple(participant: str, name: str, op_id, typed_input):
	"""WS-5 for the configuration family: grammar check and canonical
	fingerprint; identity validation happens at each call site against
	the generation that governs it."""
	if op_id is None:
		return None
	validate_op_id(op_id)
	fingerprint = hashlib.sha256(json.dumps(
		{"operation": name, "actor": participant, "input": typed_input},
		sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
	return (participant, op_id, fingerprint)


def _participant_in_document(document: dict, participant: str) -> None:
	team, dot, member = str(participant).partition(".")
	if not dot or not team or not member or \
			member not in document.get("teams", {}).get(
				team, {}).get("participants", {}):
		raise WorkError(
			f"participant {participant!r} is not a member of the "
			f"proposed generation-1 document; initialization is "
			f"committed by a named configured identity")


def init_from_config(config_path: str, *, participant: str,
                     op_id: str | None = None, refs=()) -> dict:
	"""Generation-1 bootstrap. Crash-safe by construction. WS-5: the
	required participant is validated against the PROPOSED generation-1
	document on the fresh path; on an EXISTING authority a protected
	re-init first applies that authority's current-generation identity
	gate and then performs the exact/conflicting operation lookup, so a
	lost successful response is recoverable."""
	document, digest = _read_config(config_path)
	if document["generation"] != 1:
		raise WorkError(
			f"initialization accepts generation 1; this document declares "
			f"generation {document['generation']}. A later generation implies "
			f"an authority that already accepted the earlier ones.")
	refs = _parse_config_refs(refs, document.get("roots", {}),
	                          allow_dossier=False)
	operation = _op_tuple(participant, "init", op_id,
	                      {"digest": digest, "refs": refs})
	database = _database_path(config_path)
	if os.path.lexists(database):
		if operation is not None:
			# R81: the CURRENT authority's identity gate comes first —
			# an identity its accepted generation does not know refuses
			# here, learning nothing.
			existing = Authority(database)
			try:
				# R84: one read transaction — the lookup's snapshot and
				# the identity gate observe the SAME accepted state.
				existing.conn.execute("BEGIN")
				try:
					# R85: the identity gate speaks before any lookup
					# conclusion — replay OR conflict — is disclosed.
					try:
						replay = existing._op_replay(existing.conn,
						                             *operation)
					except WorkError:
						existing._op_identity(existing.conn,
						                      participant)
						raise
					existing._op_identity(existing.conn, participant)
				finally:
					existing.conn.execute("ROLLBACK")
				if replay is not None:
					return replay
			finally:
				existing.close()
		raise WorkError(f"{database} already exists; an authority is "
		                f"initialized once. Retrying after a crash is safe "
		                f"precisely because a crashed init leaves nothing "
		                f"here.")
	_participant_in_document(document, participant)

	directory = os.path.dirname(database)
	handle, staging = tempfile.mkstemp(prefix=".work-init-", dir=directory)
	os.close(handle)
	os.unlink(staging)                      # Authority.init wants absence
	try:
		store = Authority.init(staging)
		try:
			def mutate(conn, _seq):
				_project(conn, document)
				conn.executemany(
					"INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
					[("authority_uuid",
					  document["instance"]["authority_uuid"]),
					 ("accepted_digest", digest),
					 ("accepted_generation",
					  str(document["generation"]))])
			def finish(result):
				result["database"] = database
				result["generation"] = 1
				result["digest"] = digest
				result["authority_uuid"] = \
					document["instance"]["authority_uuid"]

			outcome = store._write(
				"accept_config", participant,
				{"generation_from": None, "generation_to": 1,
				 "digest": digest,
				 "changes": _diff_summary({}, document)}, mutate,
				operation=operation, finish=finish, references=refs)
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
		finally:
			store.close()
		# THE COMMIT POINT: atomic CREATE-IF-ABSENT, never rename. R1:
		# rename replaces an existing destination, so of two concurrent
		# initializers the second silently overwrote the winner. link(2)
		# fails with EEXIST instead — the loser refuses and the winner's
		# bytes are untouched.
		try:
			os.link(staging, database)
		except FileExistsError:
			raise WorkError(
				f"{database} already exists; a concurrent initialization "
				f"won. Nothing was altered — open the winner.") from None
		os.unlink(staging)
		directory_fd = os.open(directory, os.O_RDONLY)
		try:
			os.fsync(directory_fd)
		finally:
			os.close(directory_fd)
	except BaseException:
		for leftover in (staging, staging + "-wal", staging + "-shm"):
			try:
				os.unlink(leftover)
			except OSError:
				pass
		raise
	return outcome


def open_bound(config_path: str) -> Authority:
	"""The ordinary open: config and authority must agree, exactly."""
	document, digest = _read_config(config_path)
	database = _database_path(config_path)
	store = Authority(database)
	try:
		meta = store.meta()
		if meta.get("authority_uuid") != \
				document["instance"]["authority_uuid"]:
			raise WorkError(
				f"{config_path} declares authority "
				f"{document['instance']['authority_uuid'][:12]}… but "
				f"{DATABASE} is {str(meta.get('authority_uuid'))[:12]}…; "
				f"this configuration and this authority are not a pair")
		if meta.get("accepted_digest") != digest:
			raise WorkError(
				f"{config_path} is edited but not accepted: its digest is "
				f"{digest[:12]}… and the accepted configuration is "
				f"{str(meta.get('accepted_digest'))[:12]}…. A modified "
				f"config is a proposal; accept it or restore the file.")
		if int(meta.get("accepted_generation", 0)) != document["generation"]:
			raise WorkError(
				f"{config_path} declares generation {document['generation']} "
				f"but the authority accepted "
				f"{meta.get('accepted_generation')}")
	except BaseException:
		store.close()
		raise
	return store


def _diff_summary(before_teams: dict, document: dict,
                  before_roots=frozenset()) -> dict:
	"""Structural changes, computed set-wise for the acceptance event."""
	def flatten(teams):
		identities = set()
		handlers = {}
		for team_handle, team in teams.items():
			identities.add(("team", team_handle))
			for member in team.get("participants", {}):
				identities.add(("member", f"{team_handle}.{member}"))
			for role in team.get("roles", {}):
				identities.add(("role", f"{team_handle}.{role}"))
			for route_handle, route in team.get("routes", {}).items():
				identities.add(("route", f"{team_handle}.{route_handle}"))
				# R4: the COMPLETE responsibility mapping — a role change
				# with the same handler is a structural change too.
				handlers[f"{team_handle}.{route_handle}"] = (
					route.get("role"), tuple(sorted(route.get("handlers", []))))
			for kind in team.get("kinds", {}):
				identities.add(("kind", f"{team_handle}.{kind}"))
		return identities, handlers

	old_ids, old_routing = flatten(before_teams)
	new_ids, new_routing = flatten(document["teams"])
	for root_id in document.get("roots", {}):
		new_ids.add(("root", root_id))
	for root_id in before_roots:
		old_ids.add(("root", root_id))
	return {
		"added": sorted(f"{kind}:{name}" for kind, name in new_ids - old_ids),
		"removed": sorted(f"{kind}:{name}"
		                  for kind, name in old_ids - new_ids),
		"rerouted": sorted(
			name for name in set(old_routing) & set(new_routing)
			if old_routing[name] != new_routing[name]),
	}


def _accepted_teams(store: Authority) -> dict:
	"""The currently accepted topology, re-read from the projection tables —
	acceptance validates against what the authority BELIEVES, never against
	a file somebody may have edited."""
	teams: dict = {}
	for row in store.conn.execute("SELECT * FROM teams WHERE removed=0"):
		teams[row["handle"]] = {"display": row["display"],
		                        "participants": {}, "roles": {},
		                        "routes": {}, "kinds": {}}
	for row in store.conn.execute("SELECT * FROM members WHERE removed=0"):
		if row["team"] in teams:
			teams[row["team"]]["participants"][row["handle"]] = \
				{"display": row["display"], "roles": []}
	for row in store.conn.execute("SELECT * FROM member_roles"):
		entry = teams.get(row["team"], {}).get("participants", {}) \
			.get(row["member"])
		if entry is not None:
			entry["roles"].append(row["role"])
	for row in store.conn.execute("SELECT * FROM roles WHERE removed=0"):
		if row["team"] in teams:
			teams[row["team"]]["roles"][row["handle"]] = \
				{"display": row["display"]}
	for row in store.conn.execute("SELECT * FROM routes WHERE removed=0"):
		if row["team"] in teams:
			teams[row["team"]]["routes"][row["handle"]] = \
				{"role": row["role"], "handlers": []}
	for row in store.conn.execute("SELECT * FROM route_handlers"):
		route = teams.get(row["team"], {}).get("routes", {}).get(row["route"])
		if route is not None:
			route["handlers"].append(row["member"])
	for row in store.conn.execute("SELECT * FROM kinds WHERE retired=0"):
		if row["team"] in teams:
			teams[row["team"]]["kinds"][row["handle"]] = \
				{"display": row["display"]}
	return teams


def _gate_checks(conn, document: dict) -> None:
	"""No-reuse and no-stranding, on WHATEVER connection is authoritative.

	Called twice per acceptance: once pre-lock for a fast diagnostic, and
	once INSIDE the write transaction, where it is the gate — the only place
	a check about concurrent state can be one (R2, the same lesson as the
	cycle walk and the generation recheck)."""
	reused = []
	for kind, table, extra in (("kind", "kinds", "retired=1"),
	                           ("team", "teams", "removed=1"),
	                           ("member", "members", "removed=1"),
	                           ("role", "roles", "removed=1"),
	                           ("route", "routes", "removed=1")):
		for row in conn.execute(f"SELECT * FROM {table} WHERE {extra}"):
			team_key = row["handle"] if kind == "team" else row["team"]
			name = row["handle"]
			proposal_team = document["teams"].get(
				name if kind == "team" else team_key)
			if proposal_team is None:
				continue
			if kind == "team":
				reused.append(f"team:{name}")
			elif kind == "member" and name in proposal_team["participants"]:
				reused.append(f"member:{team_key}.{name}")
			elif kind == "role" and name in proposal_team["roles"]:
				reused.append(f"role:{team_key}.{name}")
			elif kind == "route" and name in proposal_team["routes"]:
				reused.append(f"route:{team_key}.{name}")
			elif kind == "kind" and name in proposal_team["kinds"]:
				reused.append(f"kind:{team_key}.{name}")
	for row in conn.execute("SELECT root FROM roots WHERE removed=1"):
		if row["root"] in document.get("roots", {}):
			reused.append(f"root:{row['root']}")
	if reused:
		raise WorkError(
			f"the proposal reintroduces retired or removed identities "
			f"{sorted(set(reused))}; a name that left keeps its historical "
			f"meaning and is never silently reused")

	stranded = []
	surviving_kinds = {(team_handle, kind)
	                   for team_handle, team in document["teams"].items()
	                   for kind in team["kinds"]}
	for row in conn.execute(
			"SELECT id, current_team, current_kind FROM work "
			"WHERE status='open'"):
		if (row["current_team"], row["current_kind"]) not in surviving_kinds:
			stranded.append(f"work {row['id']} current "
			                f"{row['current_team']}.{row['current_kind']}")
	for row in conn.execute(
			"SELECT seq, team, kind FROM obligations WHERE status='pending'"):
		if (row["team"], row["kind"]) not in surviving_kinds:
			stranded.append(f"obligation {row['seq']} owed by "
			                f"{row['team']}.{row['kind']}")
	if stranded:
		raise WorkError(
			f"the proposal would strand: {'; '.join(sorted(stranded))}. "
			f"Responsibility is re-homed by passing or disposing first; a "
			f"configuration cannot orphan it.")


def accept_config(config_path: str, *, actor: str,
                  op_id: str | None = None, refs=()) -> dict:
	"""One audited generation+1 acceptance. The bounded exception to the
	digest refusal, and the ONLY path that changes topology or handlers."""
	document, digest = _read_config(config_path)
	database = _database_path(config_path)
	refs = _parse_config_refs(refs, document.get("roots", {}),
	                          allow_dossier=True)
	operation = _op_tuple(actor, "accept_config", op_id,
	                      {"digest": digest, "refs": refs})
	store = Authority(database)
	try:
		if operation is not None:
			# R84: one read transaction for lookup plus identity gate.
			store.conn.execute("BEGIN")
			try:
				# R85: identity refusal supersedes conflict disclosure.
				try:
					replay = store._op_replay(store.conn, *operation)
				except WorkError:
					store._op_identity(store.conn, str(actor))
					raise
				store._op_identity(store.conn, str(actor))
			finally:
				store.conn.execute("ROLLBACK")
			if replay is not None:
				return replay
		meta = store.meta()
		accepted_generation = int(meta.get("accepted_generation", 0))
		if meta.get("authority_uuid") != \
				document["instance"]["authority_uuid"]:
			raise WorkError(
				"the proposal changes instance.authority_uuid; identity is "
				"never re-assigned — a new identity is a new mailbox")
		if document["generation"] != accepted_generation + 1:
			raise WorkError(
				f"the proposal declares generation {document['generation']}; "
				f"the authority accepted {accepted_generation}, so the next "
				f"acceptable proposal is {accepted_generation + 1}. An edit "
				f"that does not say it is the next generation is a mistake, "
				f"not a proposal.")
		if digest == meta.get("accepted_digest"):
			raise WorkError("the proposal is byte-identical to the accepted "
			                "configuration; there is nothing to accept")

		# WHO MAY ACCEPT: the capability in the CURRENT generation.
		actor_team, dot, actor_member = actor.partition(".")
		if not dot:
			raise WorkError(f"actor {actor!r} is not team.member shaped")
		holds = store.conn.execute(
			"SELECT 1 FROM member_capabilities WHERE team=? AND member=? "
			"AND capability='config'", (actor_team, actor_member)).fetchone()
		current_member = store.conn.execute(
			"SELECT 1 FROM members WHERE team=? AND handle=? AND removed=0",
			(actor_team, actor_member)).fetchone()
		if current_member is None or holds is None:
			raise WorkError(
				f"{actor} does not hold the config capability in the "
				f"currently accepted generation {accepted_generation}; a "
				f"proposal cannot authorize its own acceptor")

		# R89: the store-touching dossier peek runs only AFTER the
		# identity and capability gates — a caller the accepted
		# generation refuses learns nothing about bindings; the
		# committing transaction pins the effective revision.
		from baton_work.transitions import _peek_refs
		_peek_refs(store, [ref for ref in refs
		                   if ref["kind"] == "dossier"])

		before = _accepted_teams(store)
		before_roots = {row["root"] for row in store.conn.execute(
			"SELECT root FROM roots WHERE removed=0")}
		changes = _diff_summary(before, document, before_roots)

		# Diagnostic pre-check: a fast legible refusal outside the lock. It
		# is NOT the gate — R2: a writer can commit a stranding Work between
		# this and the transaction, so the same checks run again in-lock.
		_gate_checks(store.conn, document)

		def mutate(conn, _seq):
			# THE GENERATION CHECK, AGAIN, INSIDE THE LOCK. The pre-check
			# above gives a fast legible refusal, but two concurrent
			# acceptances both pass it; the IMMEDIATE transaction is what
			# serializes them, so the losing acceptor must re-read here and
			# refuse — otherwise every racer "wins" and each writes its own
			# acceptance event (found by the 16-way race test).
			current = conn.execute(
				"SELECT value FROM meta WHERE key='accepted_generation'"
			).fetchone()
			if int(current["value"]) != document["generation"] - 1:
				raise WorkError(
					f"lost the acceptance race: generation "
					f"{current['value']} was accepted while this proposal "
					f"for {document['generation']} was being validated")
			# THE AUTHORITATIVE GATE (R2): re-run reuse + stranding against
			# the serialized state, because the pre-lock pass cannot see a
			# Work or obligation committed after it ran.
			_gate_checks(conn, document)
			_project(conn, document)
			conn.executemany(
				"INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
				[("accepted_digest", digest),
				 ("accepted_generation", str(document["generation"]))])

		def finish(result):
			result.update({"generation": document["generation"],
			               "digest": digest, "changes": changes})

		return store._write(
			"accept_config", actor,
			{"generation_from": accepted_generation,
			 "generation_to": document["generation"],
			 "digest": digest, "changes": changes}, mutate,
			operation=operation, finish=finish, references=refs)
	finally:
		store.close()
