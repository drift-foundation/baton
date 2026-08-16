"""WS-6 Slice B: the filesystem-domain operations.

`init` scaffolds an editable coordination home (valid strict JSON plus
separate Markdown instructions, no database, deliberately one-shot with
manual recovery); `activate` remains the one authoritative validation
and creation; the accepted baton.json maps portable roots to machine
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


def _rooted_config(tmp_path, roots):
	"""W4: baton.json is the single explicit root config — build and
	activate an instance whose accepted roots carry absolute bases."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {
		root_id: {"display": root_id.title(), "base": base}
		for root_id, base in roots.items()}
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	return config_path, document


# -- init: the one-shot scaffold ----------------------------------------------

def test_init_scaffolds_valid_strict_json_and_instructions(tmp_path):
	home = str(tmp_path / "home")
	os.mkdir(home)
	result = pr.scaffold_home(home)
	assert sorted(result["created"]) == ["BATON-SETUP.md", "baton.json"]
	document = _json.loads(_text(os.path.join(home, "baton.json")))
	assert document["generation"] == 1
	assert document["teams"] == {} and document["roots"] == {}
	assert len(document["instance"]["authority_uuid"]) == 32
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
	with open(os.path.join(other, "BATON-SETUP.md"), "w") as handle:
		handle.write("stale")
	with pytest.raises(bw.WorkError, match="BATON-SETUP.md"):
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

def test_the_root_base_is_explicit_strict_and_absolute(tmp_path):
	"""W4: every accepted root declares an explicit absolute base in
	baton.json — bad shapes refuse at acceptance (pure syntax), and the
	live store answers base lookups with use-time existence checks."""
	for bad_roots, needle in (
			({"Push": {"display": "X", "base": str(tmp_path)}},
			 "root ident"),
			({"pushcoin": {"display": "X", "base": "relative/path"}},
			 "absolute base"),
			({"pushcoin": {"display": "X", "base": 7}},
			 "absolute base"),
			({"pushcoin": {"display": "X"}}, "base")):
		config_path, _document = _rooted_config(tmp_path, {})
		document = _json.loads(_text(config_path))
		document["roots"] = bad_roots
		with open(config_path, "w") as handle:
			_json.dump(document, handle, indent=2, sort_keys=True)
		with pytest.raises(bw.WorkError, match=needle):
			lc.init_from_config(config_path, participant="lang.ada")

	config_path, _document = _rooted_config(
		tmp_path, {"pushcoin": str(tmp_path),
		           "drift": str(tmp_path / "nowhere")})
	lc.init_from_config(config_path, participant="lang.ada")
	# The base answer comes from the config-bound open's validated
	# document (W4 schema-preserving) — never from bare-database opens.
	store = lc.open_bound(config_path)
	try:
		assert pr.store_root_base(store, "pushcoin") == str(tmp_path)
		with pytest.raises(bw.WorkError,
		                   match="not a live configured root"):
			pr.store_root_base(store, "ghost")
		with pytest.raises(bw.WorkError,
		                   match="not an existing directory"):
			pr.store_root_base(store, "drift")
	finally:
		store.close()


# -- bootstrap: containment, idempotence, immutability -------------------------

def test_bootstrap_vendors_the_release_templates_once(tmp_path):
	base = str(tmp_path / "project")
	os.mkdir(base)
	result = pr.bootstrap_project("pushcoin", base)
	assert "tmpl/work-basic-1.md" in result["created"]
	assert os.path.isdir(os.path.join(base, "work", "open"))
	assert os.path.isdir(os.path.join(base, "work", "records"))
	vendored = _read(os.path.join(base, "tmpl", "work-basic-1.md"))
	source = _read(os.path.join(REPO, "tmpl", "work-basic-1.md"))
	assert vendored == source, "the vendored bytes differ from the release"
	# Identical re-run: everything already present, nothing rewritten.
	before = os.stat(os.path.join(base, "tmpl", "work-basic-1.md"))
	again = pr.bootstrap_project("pushcoin", base)
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
	with pytest.raises(bw.WorkError, match="never overwrites"):
		pr.bootstrap_project("pushcoin", edited)
	assert _text(os.path.join(edited, "tmpl", "work-basic-1.md")) == \
		"local specialization\n"
	# Wrong type at a managed path.
	wrong = str(tmp_path / "wrong")
	os.mkdir(wrong)
	os.mkdir(os.path.join(wrong, "tmpl"))
	os.mkdir(os.path.join(wrong, "tmpl", "work-basic-1.md"))
	with pytest.raises(bw.WorkError, match="non-file"):
		pr.bootstrap_project("pushcoin", wrong)
	# Symlink at a managed path refuses, never followed.
	linked = str(tmp_path / "linked")
	outside = str(tmp_path / "outside")
	os.mkdir(linked)
	os.mkdir(outside)
	os.symlink(outside, os.path.join(linked, "tmpl"))
	with pytest.raises(bw.WorkError, match="symlink"):
		pr.bootstrap_project("pushcoin", linked)
	assert os.listdir(outside) == [], "the symlink was followed"
	# The distribution itself is never written: the source tmpl/ holds
	# exactly what it held.
	assert _read(os.path.join(REPO, "tmpl", "work-basic-1.md")) == \
		source_bytes


def test_bootstrap_refuses_unknown_templates_and_roots(tmp_path):
	base = str(tmp_path / "project")
	os.mkdir(base)
	with pytest.raises(bw.WorkError, match="not a template shipped"):
		pr.bootstrap_project("pushcoin", base,
		                     templates=["../secrets.md"])
	with pytest.raises(bw.WorkError, match="not a template shipped"):
		pr.bootstrap_project("pushcoin", base,
		                     templates=["work-basic-99.md"])
	# The unknown-root refusal moved to the ONE root catalog: the CLI
	# resolves --root through the accepted baton.json.
	config_path, _document = _rooted_config(tmp_path,
	                                        {"pushcoin": base})
	lc.init_from_config(config_path, participant="lang.ada")
	code = work_cli.main(["--config", config_path,
	                      "bootstrap", "root=drift"])
	assert code == 1, "an unconfigured root bootstrapped"


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
	pr.bootstrap_project("pushcoin", base)
	assert hashlib.sha256(_read(database)).hexdigest() == digest, \
		"a filesystem operation wrote into the authority"
	raw = _read(database)
	# This instance accepted NO roots: a base may enter authority state
	# only through the accepted configuration, never through bootstrap.
	assert base.encode() not in raw, \
		"a bootstrap path leaked into authority state"


def test_resolve_refuses_escape_paths_and_roots_outside_the_catalog(
		tmp_path, capsys):
	"""A resolver mapping is machine-local implementation data, not a
	second root catalog. `resolve` accepts only canonical contained
	locators whose root is live in the accepted authority."""
	config_path = os.path.join(str(tmp_path), "baton.json")
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin", "base": "/srv/checkouts/pushcoin"}}
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
	accepted = []
	for locator in ("pushcoin", "pushcoin:",
	                "pushcoin:../outside",
	                f"{bound['work_id']}:../outside",
	                "ghost:docs/note.md"):
		code = work_cli.main([
			"--config", config_path, "--participant", "lang.ada",
			"resolve", f"locator={locator}"])
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
	tmpl = os.path.join(base, "tmpl")
	real_mkdir = pr.os.mkdir

	def raced_mkdir(path, *args, **kwargs):
		if path == "tmpl" and "dir_fd" in kwargs:
			os.symlink(outside, tmpl)
			raise FileExistsError(path)
		return real_mkdir(path, *args, **kwargs)

	monkeypatch.setattr(pr.os, "mkdir", raced_mkdir)
	with pytest.raises(bw.WorkError, match="symlink|changed while"):
		pr.bootstrap_project("pushcoin", base)
	assert os.listdir(outside) == [], \
		"bootstrap followed a parent symlink inserted after validation"


def test_bootstrap_reports_the_exact_partial_creation_set(tmp_path,
		monkeypatch):
	"""Every phase-two failure stops and reports what this invocation
	created; an ordinary filesystem error must not escape as a traceback
	or hide the partial result the operator now has to inspect."""
	base = str(tmp_path / "project")
	os.mkdir(base)
	real_mkdir = pr.os.mkdir

	def failing_mkdir(path, *args, **kwargs):
		if path == "work" and "dir_fd" in kwargs:
			raise PermissionError("injected phase-two refusal")
		return real_mkdir(path, *args, **kwargs)

	monkeypatch.setattr(pr.os, "mkdir", failing_mkdir)
	with pytest.raises(bw.WorkError) as caught:
		pr.bootstrap_project("pushcoin", base)
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
	assert "baton.json" in message and "BATON-SETUP.md" in message, \
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
		pr.bootstrap_project("pushcoin", base)
	assert os.listdir(outside) == [], \
		"nested mkdir followed a raced parent symlink outside the project"
	assert deleted == [], \
		f"bootstrap tried to repair an escape by deleting paths: {deleted}"


def test_the_root_catalog_is_strict_in_baton_json(tmp_path):
	"""W4: duplicate root keys and stray entry fields cannot silently
	change which checkout a root reaches — baton.json is strict."""
	config_path, document = _rooted_config(tmp_path,
	                                       {"pushcoin": str(tmp_path)})
	raw = _text(config_path)
	dup = raw.replace('"roots": {', '"roots": {"pushcoin": '
	                  '{"display": "Dup", "base": "%s"}, '
	                  % str(tmp_path), 1)
	with open(config_path, "w") as handle:
		handle.write(dup)
	with pytest.raises(bw.WorkError, match="[Dd]uplicate"):
		lc.init_from_config(config_path, participant="lang.ada")
	document["roots"]["pushcoin"]["surprise"] = True
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="unknown|stray"):
		lc.init_from_config(config_path, participant="lang.ada")


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
	real_write = pr.os.write

	def short_write(fd, data):
		return real_write(fd, data[:max(1, len(data) // 2)])

	monkeypatch.setattr(pr.os, "write", short_write)
	with pytest.raises(bw.WorkError, match="partial|short|Created"):
		pr.bootstrap_project("pushcoin", base)


def test_the_retired_resolver_flag_is_gone(tmp_path, capsys):
	"""W4 negative pin: the public grammar no longer accepts the
	machine-local resolver input; baton.json is the single root
	config."""
	config_path, _document = _rooted_config(tmp_path,
	                                        {"pushcoin": str(tmp_path)})
	lc.init_from_config(config_path, participant="lang.ada")
	for retired in ("--roots-file", "roots-file=anything.json"):
		code = work_cli.main(["--config", config_path,
		                      "--participant", "lang.ada", "resolve",
		                      "locator=pushcoin:x.md", retired])
		captured = capsys.readouterr()
		assert code == 1, f"{retired} still parses"
		assert "retired flag spelling" in captured.err or \
			"unknown key" in captured.err


def test_the_root_base_never_enters_the_schema_15_table(tmp_path):
	"""W4 R1 (schema-preserving): the accepted document is the ONE base
	source — the roots table keeps its committed schema-15 portable
	shape, and the configured absolute base is DIRECTLY absent from the
	authority bytes."""
	base = str(tmp_path / "repo-base")
	os.mkdir(base)
	config_path, _document = _rooted_config(tmp_path, {"pushcoin": base})
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	try:
		columns = [row["name"] for row in store.conn.execute(
			"PRAGMA table_info(roots)")]
		assert columns == ["root", "display", "removed"], columns
	finally:
		store.close()
	raw = _read(result["database"])
	assert base.encode() not in raw, \
		"the configured absolute base persisted into authority state"


def test_a_replaced_configuration_refuses_stale_root_resolution(tmp_path):
	"""W4 R1 race: the validated-document handoff is pinned to the open's
	digest — a configuration accepted AFTER this open refuses root
	resolution instead of serving a stale base."""
	config_path, document = _rooted_config(tmp_path,
	                                       {"pushcoin": str(tmp_path)})
	lc.init_from_config(config_path, participant="lang.ada")
	store = lc.open_bound(config_path)
	try:
		assert pr.store_root_base(store, "pushcoin") == str(tmp_path)
		document["generation"] = 2
		document["roots"]["pushcoin"]["base"] = str(tmp_path / "moved")
		with open(config_path, "w") as handle:
			_json.dump(document, handle, indent=2, sort_keys=True)
		lc.accept_config(config_path, actor="lang.ada")
		with pytest.raises(bw.WorkError, match="changed after this open"):
			pr.store_root_base(store, "pushcoin")
	finally:
		store.close()
