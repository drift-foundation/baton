"""WF-14 — the three location domains and template vendoring
(WORKFLOW-TESTS.md, WS-6 Slice B).

The DISTRIBUTION is immutable and holds the numbered templates as
sibling release assets; the machine-local resolver is explicit input
that never enters authority state; `bootstrap` vendors templates into a
resolved project root under a two-phase never-overwriting containment
model; `resolve` turns portable locators into machine paths without
mutating anything; relocation is an edit to roots.json alone.

Packaged mode drives a TEMPORARY release layout — `bin/<archive>` with
a sibling `tmpl/` copied from the source tree — because template assets
ride beside the executable (M6), never inside the zipapp.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wfdriver                                               # noqa: E402
from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document)
from ws2cast import verification_teams                        # noqa: E402

REPO = os.path.dirname(wfdriver.SRC)

ROOTS = {"pushcoin": {"display": "PushCoin monorepo"},
         "drift": {"display": "Drift checkout"}}


def _stage_release(flow, tmp_path) -> None:
	"""Packaged mode: build the temporary release layout and re-point the
	flow at the relocated archive. Source mode uses the checkout as-is."""
	if flow.mode != "packaged":
		return
	layout = os.path.join(str(tmp_path), "release")
	os.makedirs(os.path.join(layout, "bin"))
	shutil.copy2(flow.archive,
	             os.path.join(layout, "bin", "baton-work.pyz"))
	shutil.copytree(os.path.join(REPO, "tmpl"),
	                os.path.join(layout, "tmpl"))
	flow.archive = os.path.join(layout, "bin", "baton-work.pyz")


def _roots_file(directory: str, name: str, mapping: dict) -> str:
	path = os.path.join(directory, name)
	with open(path, "w", encoding="utf-8") as handle:
		json.dump({"roots": mapping}, handle)
	return path


def _read(path: str) -> bytes:
	with open(path, "rb") as handle:
		return handle.read()


def test_wf14_locations_resolver_and_bootstrap(flow, tmp_path):
	_stage_release(flow, tmp_path)
	template_source = os.path.join(REPO, "tmpl", "work-basic-1.md")
	source_bytes = _read(template_source)
	flow.init(document(verification_teams(), roots=dict(ROOTS)))

	# 1. The authority acts happen FIRST; everything after this point is
	# filesystem-domain and must leave the database byte-identical.
	push1 = flow.ok(
		"create", "--team", "push", "--kind", "bug",
		"--title", "checkout fails", "--origin", "external-report",
		"--body", "500 at checkout",
		"--binding", "pushcoin:work/records/2026/08/finding-wf14",
		viewer="push.sl")["work_id"]
	light = flow.ok("create", "--team", "push", "--kind", "bug",
	                "--title", "lightweight", "--origin",
	                "self-initiated", "--body", "no dossier",
	                viewer="push.sl")["work_id"]
	database = os.path.join(flow.directory, "work.sqlite3")
	frozen = hashlib.sha256(_read(database)).hexdigest()
	events_frozen = flow.ok("events", viewer="push.sl")

	# 2. Bootstrap vendors this release's templates into the resolved
	# project root: byte parity with the distribution in BOTH modes.
	base = os.path.join(str(tmp_path), "checkout-a")
	os.mkdir(base)
	resolver = _roots_file(str(tmp_path), "roots-main.json",
	                       {"pushcoin": base})
	vendored = flow.ok("bootstrap", "--root", "pushcoin",
	                   "--roots-file", resolver)
	assert "tmpl/work-basic-1.md" in vendored["created"]
	assert os.path.isdir(os.path.join(base, "work", "open"))
	assert os.path.isdir(os.path.join(base, "work", "records"))
	target = os.path.join(base, "tmpl", "work-basic-1.md")
	assert _read(target) == source_bytes, \
		"the vendored bytes differ from the distribution"

	# 3. An identical re-run reports already-present and rewrites
	# nothing — the inode and mtime prove no write happened.
	before = os.stat(target)
	again = flow.ok("bootstrap", "--root", "pushcoin",
	                "--roots-file", resolver)
	assert again["created"] == []
	assert "tmpl/work-basic-1.md" in again["already_present"]
	after = os.stat(target)
	assert (before.st_mtime_ns, before.st_ino) == \
		(after.st_mtime_ns, after.st_ino), "an identical re-run rewrote"

	# 4. Resolve: the Work form pins the effective binding; the relative
	# form appends dossier-relative evidence; the root form reaches the
	# vendored template itself.
	resolved = flow.ok("resolve", push1, "--roots-file", resolver,
	                   viewer="push.sl")
	assert resolved["absolute"] == os.path.join(
		base, "work", "records", "2026", "08", "finding-wf14")
	deep = flow.ok("resolve", f"{push1}:repro/checkout.log",
	               "--roots-file", resolver, viewer="push.sl")
	assert deep["absolute"] == os.path.join(
		resolved["absolute"], "repro", "checkout.log")
	shipped = flow.ok("resolve", "pushcoin:tmpl/work-basic-1.md",
	                  "--roots-file", resolver, viewer="push.sl")
	assert os.path.isfile(shipped["absolute"])

	# 5. RELOCATION is an edit to roots.json alone: the checkout moves
	# on disk, the resolver is rewritten, and every portable locator
	# resolves to the new place — the authority never notices.
	moved = os.path.join(str(tmp_path), "checkout-b")
	shutil.move(base, moved)
	resolver = _roots_file(str(tmp_path), "roots-main.json",
	                       {"pushcoin": moved})
	relocated = flow.ok("resolve", "pushcoin:tmpl/work-basic-1.md",
	                    "--roots-file", resolver, viewer="push.sl")
	assert relocated["absolute"].startswith(moved)
	assert os.path.isfile(relocated["absolute"])

	# 6. The adversarial matrix, every case a refusal that replaces
	# nothing: an unmapped root, a missing base, traversal and unknown
	# template names, a wrong type at a managed path, a symlinked
	# managed path (never followed), and conflicting bytes — a locally
	# edited template is NEVER silently upgraded to this release's.
	error = flow.refuse("bootstrap", "--root", "drift",
	                    "--roots-file", resolver)
	assert "no machine-local mapping" in error
	error = flow.refuse("resolve", "drift:docs/late.md",
	                    "--roots-file", resolver, viewer="push.sl")
	assert "no machine-local mapping" in error
	# R92: the shared contained grammar covers BOTH resolve forms, and
	# the resolver is never a second root catalog — a mapped-but-
	# unconfigured root refuses against the accepted authority.
	error = flow.refuse("resolve", "pushcoin:../outside",
	                    "--roots-file", resolver, viewer="push.sl")
	assert "contained" in error
	error = flow.refuse("resolve", f"{push1}:../outside",
	                    "--roots-file", resolver, viewer="push.sl")
	assert "contained" in error
	ghosted = _roots_file(str(tmp_path), "roots-ghost.json",
	                      {"pushcoin": moved, "ghost": moved})
	error = flow.refuse("resolve", "ghost:docs/note.md",
	                    "--roots-file", ghosted, viewer="push.sl")
	assert "not a live configured root" in error
	# R95: the independent form is ROOT_ID:relative/path — a bare root
	# or an empty suffix is not a canonical locator; only a bare WORK
	# id resolves a dossier root.
	for bare in ("pushcoin", "pushcoin:"):
		error = flow.refuse("resolve", bare, "--roots-file", resolver,
		                    viewer="push.sl")
		assert "contained" in error
	# R97: the resolver document is strict — duplicate keys and unknown
	# top-level fields refuse instead of silently redirecting a root.
	doubled = os.path.join(str(tmp_path), "roots-doubled.json")
	with open(doubled, "w", encoding="utf-8") as handle:
		handle.write('{"roots": {"pushcoin": "%s", "pushcoin": "%s"}}'
		             % (moved, moved))
	error = flow.refuse("resolve", "pushcoin:tmpl/work-basic-1.md",
	                    "--roots-file", doubled, viewer="push.sl")
	assert "duplicate" in error
	stray = os.path.join(str(tmp_path), "roots-stray.json")
	with open(stray, "w", encoding="utf-8") as handle:
		handle.write('{"roots": {"pushcoin": "%s"}, "surprise": true}'
		             % moved)
	error = flow.refuse("bootstrap", "--root", "pushcoin",
	                    "--roots-file", stray)
	assert "unknown" in error
	gone = _roots_file(str(tmp_path), "roots-gone.json",
	                   {"pushcoin": os.path.join(str(tmp_path),
	                                             "nowhere")})
	error = flow.refuse("bootstrap", "--root", "pushcoin",
	                    "--roots-file", gone)
	assert "not an existing directory" in error
	error = flow.refuse("bootstrap", "--root", "pushcoin",
	                    "--roots-file", resolver,
	                    "--template", "../secrets.md")
	assert "not a template shipped" in error
	error = flow.refuse("bootstrap", "--root", "pushcoin",
	                    "--roots-file", resolver,
	                    "--template", "work-basic-99.md")
	assert "not a template shipped" in error
	wrong = os.path.join(str(tmp_path), "wrong-type")
	os.makedirs(os.path.join(wrong, "tmpl", "work-basic-1.md"))
	error = flow.refuse(
		"bootstrap", "--root", "pushcoin", "--roots-file",
		_roots_file(str(tmp_path), "roots-wrong.json",
		            {"pushcoin": wrong}))
	assert "non-file" in error
	linked = os.path.join(str(tmp_path), "linked")
	outside = os.path.join(str(tmp_path), "outside")
	os.mkdir(linked)
	os.mkdir(outside)
	os.symlink(outside, os.path.join(linked, "tmpl"))
	error = flow.refuse(
		"bootstrap", "--root", "pushcoin", "--roots-file",
		_roots_file(str(tmp_path), "roots-linked.json",
		            {"pushcoin": linked}))
	assert "symlink" in error
	assert os.listdir(outside) == [], "the symlink was followed"
	specialized = b"# local specialization, edition frozen here\n"
	with open(os.path.join(moved, "tmpl", "work-basic-1.md"),
	          "wb") as handle:
		handle.write(specialized)
	error = flow.refuse("bootstrap", "--root", "pushcoin",
	                    "--roots-file", resolver)
	assert "never overwrites" in error
	assert _read(os.path.join(moved, "tmpl", "work-basic-1.md")) == \
		specialized, "the local edit was replaced"

	# 7. Filesystem verbs live OUTSIDE the authority: they take no
	# operation identity and no references; resolving an unbound Work
	# refuses; a reference-bearing pure read stays refused.
	error = flow.refuse("--op-id", "boot-1", "bootstrap", "--root",
	                    "pushcoin", "--roots-file", resolver)
	assert "filesystem operation" in error
	error = flow.refuse("--ref", "pushcoin:x.md", "resolve",
	                    f"{push1}", "--roots-file", resolver,
	                    viewer="push.sl")
	assert "filesystem operation" in error
	error = flow.refuse("resolve", light, "--roots-file", resolver,
	                    viewer="push.sl")
	assert "no dossier binding" in error
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "--ref", "pushcoin:x.md", "detail", push1)
	assert "pure read" in error

	# 8. Not one byte of authority state moved, and no resolver value
	# leaked into it: the database hash is unchanged across the entire
	# filesystem-domain story and holds no machine-local path.
	assert hashlib.sha256(_read(database)).hexdigest() == frozen, \
		"a filesystem operation wrote into the authority"
	raw = _read(database)
	assert b"checkout-a" not in raw and b"checkout-b" not in raw and \
		b"roots-main.json" not in raw, \
		"a resolver value leaked into authority state"
	assert flow.ok("events", viewer="push.sl") == events_frozen

	# 9. The distribution is immutable: the source tree's template holds
	# exactly its original bytes, and (packaged) the staged release
	# tmpl/ was never written back to. An archive stripped of its
	# sibling tmpl/ refuses to vendor rather than inventing assets.
	assert _read(template_source) == source_bytes
	if flow.mode == "packaged":
		assert _read(os.path.join(
			os.path.dirname(os.path.dirname(flow.archive)),
			"tmpl", "work-basic-1.md")) == source_bytes
		bare = os.path.join(str(tmp_path), "bare")
		os.mkdir(bare)
		stripped = os.path.join(bare, "baton-work.pyz")
		shutil.copy2(flow.archive, stripped)
		naked = wfdriver.Flow(flow.directory, "packaged", stripped)
		error = naked.refuse("bootstrap", "--root", "pushcoin",
		                     "--roots-file", resolver)
		assert "no template assets" in error

	assert_dense_audit(flow, "push.sl")
