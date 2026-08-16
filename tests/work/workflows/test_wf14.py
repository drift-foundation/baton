"""WF-14 — the three location domains and template vendoring
(WORKFLOW-TESTS.md, WS-6 Slice B).

The DISTRIBUTION is immutable and holds the numbered templates as
sibling release assets; the accepted baton.json is the SINGLE explicit
root config — every root declares its absolute base there (W4);
`bootstrap` vendors templates into a resolved project root under a
two-phase never-overwriting containment model; `resolve` turns portable
locators into machine paths without mutating anything; relocation is a
deliberate configuration regeneration that re-declares the base.

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

def _roots(tmp_path, pushcoin_base):
	"""The accepted catalog for this story: one real checkout, one root
	whose base does not exist, one wrong-type base, one symlinked base —
	each refusal scenario is a CONFIGURED root, resolved through the one
	catalog."""
	wrong = os.path.join(str(tmp_path), "wrong-type")
	os.makedirs(os.path.join(wrong, "tmpl", "work-basic-1.md"))
	linked = os.path.join(str(tmp_path), "linked")
	outside = os.path.join(str(tmp_path), "outside")
	os.mkdir(linked)
	os.mkdir(outside)
	os.symlink(outside, os.path.join(linked, "tmpl"))
	return {
		"pushcoin": {"display": "PushCoin monorepo",
		             "base": pushcoin_base},
		"drift": {"display": "Drift checkout",
		          "base": os.path.join(str(tmp_path), "nowhere")},
		"wrongy": {"display": "Wrong type", "base": wrong},
		"linky": {"display": "Symlinked tmpl", "base": linked},
	}, outside


def _stage_release(flow, tmp_path) -> None:
	"""Packaged mode: build the temporary release layout and re-point the
	flow at the relocated archive. Source mode uses the checkout as-is."""
	if flow.mode != "packaged":
		return
	layout = os.path.join(str(tmp_path), "release")
	os.makedirs(os.path.join(layout, "bin"))
	shutil.copy2(flow.archive,
	             os.path.join(layout, "bin", "baton.pyz"))
	shutil.copytree(os.path.join(REPO, "tmpl"),
	                os.path.join(layout, "tmpl"))
	flow.archive = os.path.join(layout, "bin", "baton.pyz")


def _read(path: str) -> bytes:
	with open(path, "rb") as handle:
		return handle.read()


def test_wf14_locations_resolver_and_bootstrap(flow, tmp_path):
	_stage_release(flow, tmp_path)
	template_source = os.path.join(REPO, "tmpl", "work-basic-1.md")
	source_bytes = _read(template_source)
	base = os.path.join(str(tmp_path), "checkout-a")
	os.mkdir(base)
	roots, outside = _roots(tmp_path, base)
	flow.init(document(verification_teams(), roots=roots))

	# 1. The authority acts happen FIRST; everything after this point is
	# filesystem-domain and must leave the database byte-identical.
	push1 = flow.ok(
		"create", "team=push", "kind=bug",
		"title=checkout fails", "origin=external-report", "classification=suspected-defect",
		"body=500 at checkout",
		"binding=pushcoin:work/records/2026/08/finding-wf14",
		viewer="push.sl")["work_id"]
	light = flow.ok("create", "team=push", "kind=bug",
	                "title=lightweight",
	                "origin=self-initiated", "classification=suspected-defect", "body=no dossier",
	                viewer="push.sl")["work_id"]
	database = os.path.join(flow.directory, "work.sqlite3")
	frozen = hashlib.sha256(_read(database)).hexdigest()
	events_frozen = flow.ok("events", viewer="push.sl")

	# 2. Bootstrap vendors this release's templates into the resolved
	# project root — the base comes from the ACCEPTED baton.json.
	vendored = flow.ok("bootstrap", "root=pushcoin")
	assert "tmpl/work-basic-1.md" in vendored["created"]
	assert os.path.isdir(os.path.join(base, "work", "open"))
	assert os.path.isdir(os.path.join(base, "work", "records"))
	target = os.path.join(base, "tmpl", "work-basic-1.md")
	assert _read(target) == source_bytes, \
		"the vendored bytes differ from the distribution"

	# 3. An identical re-run reports already-present and rewrites
	# nothing — the inode and mtime prove no write happened.
	before = os.stat(target)
	again = flow.ok("bootstrap", "root=pushcoin")
	assert again["created"] == []
	assert "tmpl/work-basic-1.md" in again["already_present"]
	after = os.stat(target)
	assert (before.st_mtime_ns, before.st_ino) == \
		(after.st_mtime_ns, after.st_ino), "an identical re-run rewrote"

	# 4. Resolve: the Work form pins the effective binding; the relative
	# form appends dossier-relative evidence; the root form reaches the
	# vendored template itself.
	resolved = flow.ok("resolve", f"locator={push1}", viewer="push.sl")
	assert resolved["absolute"] == os.path.join(
		base, "work", "records", "2026", "08", "finding-wf14")
	deep = flow.ok("resolve", f"locator={push1}:repro/checkout.log",
	               viewer="push.sl")
	assert deep["absolute"] == os.path.join(
		resolved["absolute"], "repro", "checkout.log")
	shipped = flow.ok("resolve", "locator=pushcoin:tmpl/work-basic-1.md",
	                  viewer="push.sl")
	assert os.path.isfile(shipped["absolute"])

	# 5. The filesystem verbs above changed NOTHING in the authority:
	# the database hash held across bootstrap and resolve.
	assert hashlib.sha256(_read(database)).hexdigest() == frozen, \
		"a filesystem operation wrote into the authority"
	assert flow.ok("events", viewer="push.sl") == events_frozen

	# RELOCATION is a deliberate configuration act (W4): the checkout
	# moves on disk and the base is re-declared through one accepted
	# regeneration — never a hidden machine-local file.
	moved = os.path.join(str(tmp_path), "checkout-b")
	shutil.move(base, moved)
	regen_document = document(verification_teams(), generation=2,
	                          roots=dict(roots,
	                                     pushcoin={"display":
	                                               "PushCoin monorepo",
	                                               "base": moved}))
	flow.write_config(regen_document)
	flow.ok("regen", viewer="lang.ada")
	relocated = flow.ok("resolve", "locator=pushcoin:tmpl/work-basic-1.md",
	                    viewer="push.sl")
	assert relocated["absolute"].startswith(moved)
	assert os.path.isfile(relocated["absolute"])
	frozen = hashlib.sha256(_read(database)).hexdigest()
	events_frozen = flow.ok("events", viewer="push.sl")

	# 6. The adversarial matrix, every case a refusal that replaces
	# nothing: an unmapped root, a missing base, traversal and unknown
	# template names, a wrong type at a managed path, a symlinked
	# managed path (never followed), and conflicting bytes — a locally
	# edited template is NEVER silently upgraded to this release's.
	error = flow.refuse("bootstrap", "root=ghost")
	assert "not a live configured root" in error
	error = flow.refuse("resolve", "locator=ghost:docs/late.md",
	                    viewer="push.sl")
	assert "not a live configured root" in error
	error = flow.refuse("bootstrap", "root=drift")
	assert "not an existing directory" in error
	# R92: the shared contained grammar covers BOTH resolve forms, and
	# the resolver is never a second root catalog — a mapped-but-
	# unconfigured root refuses against the accepted authority.
	error = flow.refuse("resolve", "locator=pushcoin:../outside",
	                    viewer="push.sl")
	assert "contained" in error
	error = flow.refuse("resolve", f"locator={push1}:../outside",
	                    viewer="push.sl")
	assert "contained" in error
	# R95: the independent form is ROOT_ID:relative/path — a bare root
	# or an empty suffix is not a canonical locator; only a bare WORK
	# id resolves a dossier root.
	for bare in ("pushcoin", "pushcoin:"):
		error = flow.refuse("resolve", f"locator={bare}", viewer="push.sl")
		assert "contained" in error
	error = flow.refuse("bootstrap", "root=pushcoin",
	                    "template=../secrets.md")
	assert "not a template shipped" in error
	error = flow.refuse("bootstrap", "root=pushcoin",
	                    "template=work-basic-99.md")
	assert "not a template shipped" in error
	error = flow.refuse("bootstrap", "root=wrongy")
	assert "non-file" in error
	error = flow.refuse("bootstrap", "root=linky")
	assert "symlink" in error
	assert os.listdir(outside) == [], "the symlink was followed"
	specialized = b"# local specialization, edition frozen here\n"
	with open(os.path.join(moved, "tmpl", "work-basic-1.md"),
	          "wb") as handle:
		handle.write(specialized)
	error = flow.refuse("bootstrap", "root=pushcoin")
	assert "never overwrites" in error
	assert _read(os.path.join(moved, "tmpl", "work-basic-1.md")) == \
		specialized, "the local edit was replaced"

	# 7. Filesystem verbs live OUTSIDE the authority: they take no
	# operation identity and no references; resolving an unbound Work
	# refuses; a reference-bearing pure read stays refused.
	error = flow.refuse("bootstrap", "op-id=boot-1",
	                    "root=pushcoin")
	assert "filesystem operation" in error
	error = flow.refuse("resolve", "ref=pushcoin:x.md",
	                    f"locator={push1}", viewer="push.sl")
	assert "filesystem operation" in error
	error = flow.refuse("resolve", f"locator={light}", viewer="push.sl")
	assert "no dossier binding" in error
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "detail", "ref=pushcoin:x.md", f"work={push1}")
	assert "pure read" in error

	# 8. After the deliberate relocation regen, the refusal matrix and
	# the filesystem verbs changed NOTHING further: the database hash is
	# unchanged, and bases live there ONLY through accepted
	# configuration (checkout-b via generation 2 — never a stale one).
	assert hashlib.sha256(_read(database)).hexdigest() == frozen, \
		"a filesystem operation wrote into the authority"
	raw = _read(database)
	assert b"checkout-a" not in raw, \
		"the superseded base survived the accepted relocation"
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
		stripped = os.path.join(bare, "baton.pyz")
		shutil.copy2(flow.archive, stripped)
		naked = wfdriver.Flow(flow.directory, "packaged", stripped)
		error = naked.refuse("bootstrap", "root=pushcoin")
		assert "no template assets" in error

	assert_dense_audit(flow, "push.sl")
