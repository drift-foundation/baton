"""WS-6 Slice B: the filesystem-domain operations.

`init` scaffolds an editable coordination home (valid strict JSON plus
separate Markdown instructions, no database, deliberately one-shot with
manual recovery); `activate` remains the one authoritative validation
and creation; the explicit resolver maps portable roots to machine
bases without ever touching authority state; `bootstrap` vendors this
release's numbered templates into one resolved project root under a
two-phase never-overwriting containment model.
"""

from __future__ import annotations

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import project as pr                          # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402

import json as _json

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))


def _read(path):
	with open(path, "rb") as handle:
		return handle.read()


def _text(path):
	with open(path, "r", encoding="utf-8") as handle:
		return handle.read()


_RESOLVER_COUNT = [0]


def _resolver(tmp_path, mapping):
	_RESOLVER_COUNT[0] += 1
	path = os.path.join(str(tmp_path),
	                    f"roots-{_RESOLVER_COUNT[0]}.json")
	with open(path, "w") as handle:
		_json.dump({"roots": mapping}, handle)
	return path


# -- init: the one-shot scaffold ----------------------------------------------

def test_init_scaffolds_valid_strict_json_and_instructions(tmp_path):
	home = str(tmp_path / "home")
	os.mkdir(home)
	result = pr.scaffold_home(home)
	assert sorted(result["created"]) == ["BATON-SETUP.md", "baton.json",
	                                     "roots.json"]
	document = _json.loads(_text(os.path.join(home, "baton.json")))
	assert document["generation"] == 1
	assert document["teams"] == {} and document["roots"] == {}
	assert len(document["instance"]["authority_uuid"]) == 32
	resolver = _json.loads(_text(os.path.join(home, "roots.json")))
	assert resolver == {"roots": {}}
	assert "baton activate" in _text(
		os.path.join(home, "BATON-SETUP.md"))
	assert not os.path.exists(os.path.join(home, "work.sqlite3")), \
		"the scaffold created a database"
	# Activation of the PRISTINE scaffold refuses with the real
	# semantic message and leaves nothing.
	with pytest.raises(bw.WorkError, match="teams must not be empty"):
		lc.init_from_config(os.path.join(home, "baton.json"),
		                    participant="lang.ada")
	assert not os.path.exists(os.path.join(home, "work.sqlite3"))


def test_init_is_one_shot_and_names_the_blockers(tmp_path):
	home = str(tmp_path / "home")
	os.mkdir(home)
	pr.scaffold_home(home)
	with pytest.raises(bw.WorkError,
	                   match="manual cleanup|already contains"):
		pr.scaffold_home(home)
	# A single stray managed file blocks too, BY NAME — init never
	# adopts or resumes.
	other = str(tmp_path / "other")
	os.mkdir(other)
	with open(os.path.join(other, "roots.json"), "w") as handle:
		handle.write("{}")
	with pytest.raises(bw.WorkError, match="roots.json"):
		pr.scaffold_home(other)
	# A missing directory refuses rather than inventing it.
	with pytest.raises(bw.WorkError, match="not an existing directory"):
		pr.scaffold_home(str(tmp_path / "absent"))


def test_the_scaffold_then_edit_then_activate_flow(tmp_path):
	home = str(tmp_path / "home")
	os.mkdir(home)
	pr.scaffold_home(home)
	config_path = os.path.join(home, "baton.json")
	document = _json.loads(_text(config_path))
	full = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["teams"] = full["teams"]
	document["instance"]["name"] = "edited"
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada",
	                             op_id="activate-1")
	assert result["generation"] == 1
	assert result["authority_uuid"] == \
		document["instance"]["authority_uuid"]
	replay = lc.init_from_config(config_path, participant="lang.ada",
	                             op_id="activate-1")
	assert replay["operation"]["state"] == "replayed"


# -- the resolver --------------------------------------------------------------

def test_the_resolver_is_explicit_strict_and_absolute(tmp_path):
	good = _resolver(tmp_path, {"pushcoin": str(tmp_path)})
	assert pr.load_resolver(good) == {"pushcoin": str(tmp_path)}
	for bad_mapping, needle in (
			({"Push": str(tmp_path)}, "root ident"),
			({"pushcoin": "relative/path"}, "ABSOLUTE"),
			({"pushcoin": 7}, "ABSOLUTE")):
		path = _resolver(tmp_path, bad_mapping)
		with pytest.raises(bw.WorkError, match=needle):
			pr.load_resolver(path)
	with pytest.raises(bw.WorkError, match="cannot read"):
		pr.load_resolver(str(tmp_path / "missing.json"))
	mapping = pr.load_resolver(good)
	with pytest.raises(bw.WorkError, match="no machine-local mapping"):
		pr.resolve_base(mapping, "drift")
	gone = _resolver(tmp_path, {"drift": str(tmp_path / "nowhere")})
	with pytest.raises(bw.WorkError, match="not an existing directory"):
		pr.resolve_base(pr.load_resolver(gone), "drift")


# -- bootstrap: containment, idempotence, immutability -------------------------

def test_bootstrap_vendors_the_release_templates_once(tmp_path):
	base = str(tmp_path / "project")
	os.mkdir(base)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	result = pr.bootstrap_project("pushcoin", resolver)
	assert "tmpl/work-basic-1.md" in result["created"]
	assert os.path.isdir(os.path.join(base, "work", "open"))
	assert os.path.isdir(os.path.join(base, "work", "records"))
	vendored = _read(os.path.join(base, "tmpl", "work-basic-1.md"))
	source = _read(os.path.join(REPO, "tmpl", "work-basic-1.md"))
	assert vendored == source, "the vendored bytes differ from the release"
	# Identical re-run: everything already present, nothing rewritten.
	before = os.stat(os.path.join(base, "tmpl", "work-basic-1.md"))
	again = pr.bootstrap_project("pushcoin", resolver)
	assert again["created"] == []
	assert "tmpl/work-basic-1.md" in again["already_present"]
	after = os.stat(os.path.join(base, "tmpl", "work-basic-1.md"))
	assert (before.st_mtime_ns, before.st_ino) == \
		(after.st_mtime_ns, after.st_ino), "an identical re-run rewrote"


def test_bootstrap_refuses_conflicts_types_symlinks_and_escapes(tmp_path):
	source_bytes = _read(os.path.join(REPO, "tmpl", "work-basic-1.md"))
	# Conflicting bytes: an edited vendored template never gets
	# replaced — adopting a newer standard is an explicit change.
	edited = str(tmp_path / "edited")
	os.makedirs(os.path.join(edited, "tmpl"))
	with open(os.path.join(edited, "tmpl", "work-basic-1.md"),
	          "w") as handle:
		handle.write("local specialization\n")
	resolver = _resolver(tmp_path, {"pushcoin": edited})
	with pytest.raises(bw.WorkError, match="never overwrites"):
		pr.bootstrap_project("pushcoin", resolver)
	assert _text(os.path.join(edited, "tmpl", "work-basic-1.md")) == \
		"local specialization\n"
	# Wrong type at a managed path.
	wrong = str(tmp_path / "wrong")
	os.mkdir(wrong)
	os.mkdir(os.path.join(wrong, "tmpl"))
	os.mkdir(os.path.join(wrong, "tmpl", "work-basic-1.md"))
	with pytest.raises(bw.WorkError, match="non-file"):
		pr.bootstrap_project(
			"pushcoin", _resolver(tmp_path, {"pushcoin": wrong}))
	# Symlink at a managed path refuses, never followed.
	linked = str(tmp_path / "linked")
	outside = str(tmp_path / "outside")
	os.mkdir(linked)
	os.mkdir(outside)
	os.symlink(outside, os.path.join(linked, "tmpl"))
	with pytest.raises(bw.WorkError, match="symlink"):
		pr.bootstrap_project(
			"pushcoin", _resolver(tmp_path, {"pushcoin": linked}))
	assert os.listdir(outside) == [], "the symlink was followed"
	# The distribution itself is never written: the source tmpl/ holds
	# exactly what it held.
	assert _read(os.path.join(REPO, "tmpl", "work-basic-1.md")) == \
		source_bytes


def test_bootstrap_refuses_unknown_templates_and_roots(tmp_path):
	base = str(tmp_path / "project")
	os.mkdir(base)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	with pytest.raises(bw.WorkError, match="not a template shipped"):
		pr.bootstrap_project("pushcoin", resolver,
		                     templates=["../secrets.md"])
	with pytest.raises(bw.WorkError, match="not a template shipped"):
		pr.bootstrap_project("pushcoin", resolver,
		                     templates=["work-basic-99.md"])
	with pytest.raises(bw.WorkError, match="no machine-local mapping"):
		pr.bootstrap_project("drift", resolver)


def test_filesystem_operations_never_touch_authority_state(tmp_path):
	"""The resolver and bootstrap live outside the authority: no byte
	of an activated database changes, and no resolver value enters it."""
	home = str(tmp_path / "home")
	os.mkdir(home)
	pr.scaffold_home(home)
	config_path = os.path.join(home, "baton.json")
	document = _json.loads(_text(config_path))
	document["teams"] = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	activated = lc.init_from_config(config_path,
	                                participant="lang.ada")
	database = activated["database"]
	digest = hashlib.sha256(_read(database)).hexdigest()
	base = str(tmp_path / "project")
	os.mkdir(base)
	pr.bootstrap_project(
		"pushcoin", _resolver(tmp_path, {"pushcoin": base}))
	assert hashlib.sha256(_read(database)).hexdigest() == digest, \
		"a filesystem operation wrote into the authority"
	raw = _read(database)
	assert base.encode() not in raw and b"roots.json" not in raw, \
		"a resolver value leaked into authority state"


def test_resolve_refuses_escape_paths_and_roots_outside_the_catalog(
		tmp_path, capsys):
	"""A resolver mapping is machine-local implementation data, not a
	second root catalog. `resolve` accepts only canonical contained
	locators whose root is live in the accepted authority."""
	config_path = os.path.join(str(tmp_path), "baton.json")
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	bound = tr.create_work(
		store, team="lang", kind="bug", title="bound",
		origin="external-report", classification="suspected-defect",
		author="ada", body="evidence",
		binding="pushcoin:work/records/2026/08/finding-resolve")
	store.close()
	base = str(tmp_path / "project")
	os.mkdir(base)
	resolver = _resolver(tmp_path, {"pushcoin": base, "ghost": base})

	accepted = []
	for locator in ("pushcoin", "pushcoin:",
	                "pushcoin:../outside",
	                f"{bound['work_id']}:../outside",
	                "ghost:docs/note.md"):
		code = work_cli.main([
			"--config", config_path, "--participant", "lang.ada",
			"resolve", locator, "--roots-file", resolver])
		captured = capsys.readouterr()
		if code == 0:
			accepted.append((locator, _json.loads(captured.out)["result"]))
		else:
			error = _json.loads(captured.err)["error"]
			assert "contained" in error or \
				"live configured root" in error, error
	assert accepted == [], \
		f"resolve accepted non-canonical locators: {accepted}"


def test_bootstrap_refuses_a_parent_symlink_inserted_after_validation(
		tmp_path, monkeypatch):
	"""The phase boundary is adversarial: a validated absent directory
	may become a symlink before mkdir. Creation must use the ruled
	O_NOFOLLOW dir-fd chain and never follow it outside the project."""
	base = str(tmp_path / "project")
	outside = str(tmp_path / "outside")
	os.mkdir(base)
	os.mkdir(outside)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	tmpl = os.path.join(base, "tmpl")
	real_mkdir = pr.os.mkdir

	def raced_mkdir(path, *args, **kwargs):
		if path == "tmpl" and "dir_fd" in kwargs:
			os.symlink(outside, tmpl)
			raise FileExistsError(path)
		return real_mkdir(path, *args, **kwargs)

	monkeypatch.setattr(pr.os, "mkdir", raced_mkdir)
	with pytest.raises(bw.WorkError, match="symlink|changed while"):
		pr.bootstrap_project("pushcoin", resolver)
	assert os.listdir(outside) == [], \
		"bootstrap followed a parent symlink inserted after validation"


def test_bootstrap_reports_the_exact_partial_creation_set(tmp_path,
		monkeypatch):
	"""Every phase-two failure stops and reports what this invocation
	created; an ordinary filesystem error must not escape as a traceback
	or hide the partial result the operator now has to inspect."""
	base = str(tmp_path / "project")
	os.mkdir(base)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	real_mkdir = pr.os.mkdir

	def failing_mkdir(path, *args, **kwargs):
		if path == "work" and "dir_fd" in kwargs:
			raise PermissionError("injected phase-two refusal")
		return real_mkdir(path, *args, **kwargs)

	monkeypatch.setattr(pr.os, "mkdir", failing_mkdir)
	with pytest.raises(bw.WorkError) as caught:
		pr.bootstrap_project("pushcoin", resolver)
	assert "created" in str(caught.value).lower()
	assert "tmpl" in str(caught.value), \
		"the refusal omitted the directory this invocation created"


def test_init_reports_even_the_file_whose_write_failed(tmp_path,
		monkeypatch):
	"""O_EXCL creates the target before its bytes are written. A write
	failure therefore reports that partial target as created, along with
	every earlier companion, for deliberate manual cleanup."""
	home = str(tmp_path / "home")
	os.mkdir(home)
	real_write = pr.os.write
	calls = {"count": 0}

	def failing_write(fd, data):
		calls["count"] += 1
		if calls["count"] == 2:
			raise OSError("injected scaffold write failure")
		return real_write(fd, data)

	monkeypatch.setattr(pr.os, "write", failing_write)
	with pytest.raises(bw.WorkError) as caught:
		pr.scaffold_home(home)
	message = str(caught.value)
	assert "roots.json" in message and "BATON-SETUP.md" in message, \
		f"the partial scaffold report is incomplete: {message}"


def test_bootstrap_creates_nested_directories_through_the_no_follow_chain(
		tmp_path, monkeypatch):
	"""No-follow must govern creation, not only EEXIST revalidation. A
	validated parent swapped before nested mkdir must not redirect the
	new directory outside the project."""
	base = str(tmp_path / "project")
	outside = str(tmp_path / "outside")
	os.mkdir(base)
	os.mkdir(outside)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	work = os.path.join(base, "work")
	real_mkdir = pr.os.mkdir
	real_rmdir = pr.os.rmdir
	deleted = []

	def raced_nested_mkdir(path, *args, **kwargs):
		if path == "open" and "dir_fd" in kwargs:
			real_rmdir(work)
			os.symlink(outside, work)
		return real_mkdir(path, *args, **kwargs)

	def observed_rmdir(path, *args, **kwargs):
		deleted.append(path)
		return real_rmdir(path, *args, **kwargs)

	monkeypatch.setattr(pr.os, "mkdir", raced_nested_mkdir)
	monkeypatch.setattr(pr.os, "rmdir", observed_rmdir)
	with pytest.raises(bw.WorkError, match="symlink|changed while"):
		pr.bootstrap_project("pushcoin", resolver)
	assert os.listdir(outside) == [], \
		"nested mkdir followed a raced parent symlink outside the project"
	assert deleted == [], \
		f"bootstrap tried to repair an escape by deleting paths: {deleted}"


def test_the_resolver_document_is_strict_json(tmp_path):
	"""Duplicate mappings and unknown top-level fields cannot silently
	change which checkout a portable root reaches."""
	base = str(tmp_path)
	for index, raw in enumerate((
			'{"roots":{"pushcoin":"%s","pushcoin":"%s"}}' %
			(base, base),
			'{"roots":{},"surprise":true}')):
		path = str(tmp_path / f"strict-{index}.json")
		with open(path, "w") as handle:
			handle.write(raw)
		with pytest.raises(bw.WorkError, match="duplicate|unknown"):
			pr.load_resolver(path)


def test_init_refuses_and_reports_a_short_write(tmp_path, monkeypatch):
	"""os.write may legally return fewer bytes without raising. Init
	must finish the write or report the partial managed file."""
	home = str(tmp_path / "home")
	os.mkdir(home)
	real_write = pr.os.write

	def short_write(fd, data):
		return real_write(fd, data[:max(1, len(data) // 2)])

	monkeypatch.setattr(pr.os, "write", short_write)
	with pytest.raises(bw.WorkError, match="partial|short|Created"):
		pr.scaffold_home(home)


def test_bootstrap_refuses_and_reports_a_short_write(tmp_path, monkeypatch):
	"""A successful bootstrap guarantees byte-identical vendoring; a
	short write is a reported partial failure, never success."""
	base = str(tmp_path / "project")
	os.mkdir(base)
	resolver = _resolver(tmp_path, {"pushcoin": base})
	real_write = pr.os.write

	def short_write(fd, data):
		return real_write(fd, data[:max(1, len(data) // 2)])

	monkeypatch.setattr(pr.os, "write", short_write)
	with pytest.raises(bw.WorkError, match="partial|short|Created"):
		pr.bootstrap_project("pushcoin", resolver)
