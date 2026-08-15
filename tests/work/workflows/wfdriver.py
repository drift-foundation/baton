"""The shared workflow process driver and scenario builders.

Workflow acceptance (WORKFLOW-TESTS.md test discipline): every act is a
SEPARATE PROCESS of the public JSON CLI, seeded from one explicit
`baton.json`, never through internal registry calls. The driver runs in two
modes — `source` (the checkout via `-m baton_work.cli`) and `packaged` (a
zipapp artifact with PYTHONPATH stripped) — and every workflow runs in both.

Builders and the driver live here; assertions live in the test files.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipapp

SRC = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__))))),
	"src")

UUID = "ab" * 16


def build_archive(directory: str) -> str:
	"""The built artifact the packaged mode drives — same sources, entered
	only through the archive."""
	staging = os.path.join(directory, "app")
	shutil.copytree(os.path.join(SRC, "baton_work"),
	                os.path.join(staging, "baton_work"))
	target = os.path.join(directory, "baton-work.pyz")
	# cli:entry, NOT cli:main — zipapp discards the target's return value,
	# so main-as-target exits 0 on refusals (WF-06 found this; the focused
	# regression lives in test_packaged.py).
	zipapp.create_archive(staging, target, interpreter=None,
	                      main="baton_work.cli:entry")
	return target


class Flow:
	"""One workflow instance: a config file, an authority beside it, and a
	way to run acts as separate CLI processes."""

	def __init__(self, directory: str, mode: str, archive: str):
		assert mode in ("source", "packaged")
		self.directory = str(directory)
		self.mode = mode
		self.archive = archive
		self.config_path = os.path.join(self.directory, "baton.json")
		# WS-2 group 3: the deterministic clock seam. When set, child
		# processes see BATON_WORK_NOW and the authority derives due-ness
		# from this exact instant instead of the wall clock.
		self.now: str | None = None

	# -- process plumbing --------------------------------------------------

	def _argv(self) -> list[str]:
		if self.mode == "packaged":
			return [sys.executable, self.archive]
		return [sys.executable, "-m", "baton_work.cli"]

	def _env(self) -> dict:
		env = {key: value for key, value in os.environ.items()
		       if key not in ("PYTHONPATH", "BATON_WORK_NOW")}
		if self.mode == "source":
			env["PYTHONPATH"] = SRC
		if self.now is not None:
			env["BATON_WORK_NOW"] = self.now
		return env

	def raw(self, *argv, viewer: str | None = None):
		command = self._argv() + ["--config", self.config_path]
		if viewer:
			command += ["--participant", viewer]
		command += list(argv)
		return subprocess.run(command, capture_output=True, text=True,
		                      timeout=120, env=self._env())

	def spawn(self, *argv, viewer: str | None = None) -> subprocess.Popen:
		"""A concurrent act for race checkpoints; join with `finish`."""
		command = self._argv() + ["--config", self.config_path]
		if viewer:
			command += ["--participant", viewer]
		command += list(argv)
		return subprocess.Popen(command, stdout=subprocess.PIPE,
		                        stderr=subprocess.PIPE, text=True,
		                        env=self._env())

	@staticmethod
	def finish(proc: subprocess.Popen):
		out, err = proc.communicate(timeout=120)
		return proc.returncode, out, err

	# -- the two outcomes a checkpoint asserts -----------------------------

	def ok(self, *argv, viewer: str | None = None) -> dict:
		proc = self.raw(*argv, viewer=viewer)
		assert proc.returncode == 0, \
			f"{argv} refused: {proc.stderr or proc.stdout}"
		return json.loads(proc.stdout)["result"]

	def refuse(self, *argv, viewer: str | None = None) -> str:
		proc = self.raw(*argv, viewer=viewer)
		assert proc.returncode == 1, \
			f"{argv} did not refuse: {proc.stdout}"
		error = json.loads(proc.stderr)["error"]
		assert isinstance(error, str) and error
		return error

	def born(self, work_id: str, viewer: str) -> str:
		"""The Work's first related discussion, via the public paged
		verb — story shorthand, two real CLI calls underneath."""
		return self.ok("work-discussions", work_id, "--limit", "1",
		               viewer=viewer)["rows"][0]["id"]

	def post(self, work_id: str, *argv, viewer: str) -> dict:
		"""WS-1-era story shorthand: say into the Work's first related
		discussion. Both calls go through the public CLI surface."""
		return self.ok("say", self.born(work_id, viewer), *argv,
		               viewer=viewer)

	def envelope(self, *argv, viewer: str | None = None) -> dict:
		proc = self.raw(*argv, viewer=viewer)
		assert proc.returncode == 0, proc.stderr or proc.stdout
		return json.loads(proc.stdout)

	# -- scenario seeding --------------------------------------------------

	def write_config(self, document: dict) -> None:
		with open(self.config_path, "w", encoding="utf-8") as handle:
			json.dump(document, handle, indent=2, sort_keys=True)
			handle.write("\n")

	def init(self, document: dict) -> dict:
		self.write_config(document)
		return self.ok("init")


# -- configuration builders ----------------------------------------------

def team(display: str, participants: dict, roles: dict, routes: dict,
         kinds: dict) -> dict:
	return {"display": display, "participants": participants,
	        "roles": roles, "routes": routes, "kinds": kinds}


def document(teams: dict, *, generation: int = 1, uuid: str = UUID,
             name: str = "workflow") -> dict:
	return {"config_version": 1, "protocol_version": 11,
	        "generation": generation,
	        "instance": {"name": name, "authority_uuid": uuid,
	                     "database": "work.sqlite3"},
	        "teams": teams}


def standard_teams() -> dict:
	"""The workflow cast: Lang (provider with real per-phase routes), three
	consumers, and an operations team. Route names are operational, not
	`main` — WF-08 reroutes `intake` by name."""
	return {
		"lang": team(
			"Lang",
			{"ada": {"display": "Ada", "roles": ["rsrch", "impl", "rev"],
			         "capabilities": ["config"]},
			 "grace": {"display": "Grace", "roles": ["rsrch", "impl"]}},
			{"rsrch": {"display": "Research"},
			 "impl": {"display": "Implementation"},
			 "rev": {"display": "Review"}},
			{"intake": {"role": "rsrch", "handlers": ["ada"]},
			 "build": {"role": "impl", "handlers": ["grace"]},
			 "review": {"role": "rev", "handlers": ["ada"]}},
			{"bug": {"display": "Bug", "route": "intake"},
			 "rsrch": {"display": "Research", "route": "intake"},
			 "impl": {"display": "Implement", "route": "build"},
			 "rev": {"display": "Review", "route": "review"}}),
		"push": team(
			"Pushcoin",
			{"sl": {"display": "Slawomir", "roles": ["dev"],
			        "capabilities": ["config"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["sl"]}},
			{"bug": {"display": "Bug", "route": "main"},
			 "rev": {"display": "Review", "route": "main"}}),
		"web": team(
			"Web",
			{"wren": {"display": "Wren", "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["wren"]}},
			{"bug": {"display": "Bug", "route": "main"}}),
		"mdb": team(
			"MariaDB",
			{"mo": {"display": "Mo", "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["mo"]}},
			{"bug": {"display": "Bug", "route": "main"},
			 "build": {"display": "Build", "route": "main"}}),
		"ops": team(
			"Operations",
			{"bat": {"display": "Baton", "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["bat"]}},
			{"ops": {"display": "Operations", "route": "main"}}),
	}


# -- shared checkpoint assertions (discipline 5 and 7) ----------------------

def assert_dense_audit(flow: Flow, viewer: str) -> list[dict]:
	events = flow.ok("events", viewer=viewer)
	seqs = [event["seq"] for event in events]
	assert seqs == list(range(1, len(seqs) + 1)), \
		"the audit sequence has a hole"
	return events


def assert_final_invariants(flow: Flow, viewer: str, work_ids) -> list[dict]:
	"""Discipline 7: ordered audit; every open Work has exactly one Current;
	a terminal Work has neither Current nor Next."""
	events = assert_dense_audit(flow, viewer)
	for work_id in work_ids:
		detail = flow.ok("detail", work_id, viewer=viewer)
		if detail["status"] == "open":
			assert detail["current"] is not None and \
				detail["current"]["endpoint"], \
				f"open {work_id} has no Current endpoint"
		else:
			assert detail["current"] is None and detail["next"] is None, \
				f"terminal {work_id} retains an endpoint"
	return events


def assert_refusal_changes_nothing(flow: Flow, viewer: str, *argv,
                                   as_viewer: str | None = None) -> str:
	"""Discipline 5: a refused act leaves no partial rows and no sequence
	hole — the audit trail is byte-identical around it."""
	before = flow.ok("events", viewer=viewer)
	error = flow.refuse(*argv, viewer=as_viewer or viewer)
	after = flow.ok("events", viewer=viewer)
	assert after == before, "a refused operation changed the authority"
	return error
