"""A synthetic, internally coherent release candidate, built in the test.

Shared by the deployment suites because both need the same thing: a candidate
they can make exactly ONE thing wrong in, and a SECOND candidate that is
genuinely different from the first. Nothing here fabricates a release
directory — the projection checks in `verify_release` exist precisely to make
a hand-made release impossible, so a test that needs two releases must build
two candidates and install them.
"""

from __future__ import annotations

import hashlib
import json


def _sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


CATALOG = {
	"format": "baton.products",
	"format_version": 1,
	"protocol_version": 11,
	"core": {"version": "1.1.0", "api_version": 3},
	"floors": {"python_min": "3.11", "sqlite_min": "3.37.0"},
	"products": {
		"baton": {"artifact": "bin/baton", "version": "11.1.0",
		          "requires_core_api": 3},
		"baton-tui": {"artifact": "bin/baton-tui", "version": "11.4.0",
		              "requires_core_api": 3},
	},
}


def _zipapp(extra: dict) -> tuple[bytes, dict]:
	"""A MINIMAL BUT REAL zipapp, and the members inside it.

	Real rather than pretend, because certification now opens the archive and
	checks the manifest's claims against the catalog and core members it
	actually carries. A fixture of `b"# pretend cli"` could not express the
	defect class this exists to catch: a manifest whose bytes are honest and
	whose claims are not."""
	import io
	import zipfile

	members = {
		"baton_core/products.json": json.dumps(CATALOG, sort_keys=True,
		                                       indent=2).encode() + b"\n",
		"baton_core/_impl.py": b"# pretend implementation\n",
		"baton_core/__init__.py": b"# pretend package\n",
	}
	members.update(extra)
	buffer = io.BytesIO()
	buffer.write(b"#!/usr/bin/env python3\n")
	with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
		for name, data in sorted(members.items()):
			info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
			info.external_attr = 0o644 << 16
			archive.writestr(info, data)
	return buffer.getvalue(), members


def _core_digest(members: dict) -> str:
	"""Name then bytes, sorted -- the builder's rule, restated here because a
	fixture that borrowed the implementation could not disagree with it."""
	digest = hashlib.sha256()
	for name in sorted(m for m in members if m.startswith("baton_core/")):
		digest.update(name.encode("utf-8"))
		digest.update(members[name])
	return digest.hexdigest()


def candidate_tree(tmp_path):
	"""A minimal, internally consistent candidate tree.

	Built rather than copied so a test can make exactly one thing wrong and
	watch the gate refuse it. The two artifacts are real zipapps carrying the
	same catalog and the same core members, with DELIBERATELY DIFFERENT product
	versions -- CLI 11.1.0, console 11.4.0 -- because a fixture where both
	numbers matched would let a rule that still required equality pass
	unnoticed."""
	source = tmp_path / "source"
	(source / "bin").mkdir(parents=True)
	(source / "docs").mkdir()
	(source / "dist").mkdir()
	(source / "examples").mkdir()

	cli, cli_members = _zipapp({"__main__.py": b"# cli bootstrap\n"})
	tui, tui_members = _zipapp({"__main__.py": b"# console bootstrap\n",
	                            "baton_tui/__init__.py": b"# pretend console\n"})
	proto = b"# the protocol\n"
	(source / "bin" / "baton").write_bytes(cli)
	(source / "bin" / "baton-tui").write_bytes(tui)
	(source / "docs" / "AGENTS-MAILBOX-PROTO.md").write_bytes(proto)
	(source / "docs" / "EFFECTIVE-BATON.md").write_bytes(b"# using it\n")
	(source / "docs" / "RELEASE-baton-11.1.0.md").write_bytes(b"# baton 11.1.0\n")
	(source / "docs" / "RELEASE-baton-tui-11.4.0.md").write_bytes(
		b"# baton-tui 11.4.0\n")
	(source / "README.md").write_bytes(b"# baton\n")
	(source / "LICENSE").write_bytes(b"a licence\n")
	(source / "examples" / "baton.json").write_text(json.dumps({
		"config_version": 1, "protocol_version": 11, "generation": 1,
		"mailbox": {"name": "example"},
		"participants": {"team.implementer": {}, "team.reviewer": {}},
		"roots": {}, "retention_days": 90}))
	core = {"version": "1.1.0", "api_version": 3,
	        "package_sha256": _core_digest(cli_members)}
	assert core["package_sha256"] == _core_digest(tui_members), \
		"both artifacts must embed the same core for the fixture to be coherent"
	(source / "dist" / "DISTRIBUTION.json").write_text(json.dumps({
		"tool": "baton", "artifact": "bin/baton", "artifact_sha256": _sha(cli),
		"product_version": "11.1.0", "protocol_version": 11,
		"requires_core_api": 3, "embeds_core": core,
		"python_min": "3.11", "sqlite_min": "3.37.0",
		"source_sha256": _sha(cli_members["baton_core/_impl.py"]),
		"protocol_doc": "docs/AGENTS-MAILBOX-PROTO.md",
		"protocol_doc_sha256": _sha(proto)}, indent=2))
	(source / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps({
		"tool": "baton-tui", "artifact": "bin/baton-tui",
		"artifact_sha256": _sha(tui),
		"product_version": "11.4.0", "protocol_version": 11,
		"requires_core_api": 3, "embeds_core": core,
		"python_min": "3.11", "sqlite_min": "3.37.0",
		"members": sorted(tui_members),
		"protocol_doc": "docs/AGENTS-MAILBOX-PROTO.md",
		"protocol_doc_sha256": _sha(proto)}, indent=2))
	return source


def rebuild(source, manifest_name, tool, catalog=None, extra=None,
            **manifest_changes):
	"""Rebuild one product from a modified catalog, manifest and all.

	Certification now opens the archive and checks the manifest against the
	catalog inside it, so a test that changes only a manifest field is testing
	that check rather than whatever it meant to test. This produces a
	COHERENT alternative product: the artifact really carries the changed
	catalog, and its manifest really describes the artifact."""
	global CATALOG
	document = json.loads(json.dumps(CATALOG)) if catalog is None else catalog
	original, CATALOG = CATALOG, document
	try:
		contents = {"__main__.py": b"# bootstrap\n"}
		if tool == "baton-tui":
			contents["baton_tui/__init__.py"] = b"# pretend console\n"
		contents.update(extra or {})
		payload, members = _zipapp(contents)
	finally:
		CATALOG = original
	entry = document["products"][tool]
	(source / entry["artifact"]).write_bytes(payload)
	manifest = json.loads((source / "dist" / manifest_name).read_text())
	manifest.update({
		"artifact": entry["artifact"],
		"artifact_sha256": _sha(payload),
		"product_version": entry["version"],
		"requires_core_api": entry["requires_core_api"],
		"protocol_version": document["protocol_version"],
		"python_min": document["floors"]["python_min"],
		"sqlite_min": document["floors"]["sqlite_min"],
		"embeds_core": {"version": document["core"]["version"],
		                "api_version": document["core"]["api_version"],
		                "package_sha256": _core_digest(members)},
	})
	if "source_sha256" in manifest:
		manifest["source_sha256"] = _sha(members["baton_core/_impl.py"])
	if "members" in manifest:
		manifest["members"] = sorted(members)
	manifest.update(manifest_changes)
	(source / "dist" / manifest_name).write_text(json.dumps(manifest, indent=2))
	return manifest




LEGACY_CATALOG = {
	"format": "baton.products",
	"format_version": 1,
	"protocol_version": 10,
	"core": {"version": "1.1.0", "api_version": 3},
	"floors": {"python_min": "3.11", "sqlite_min": "3.37.0"},
	"products": {
		"baton": {"artifact": "bin/baton", "version": "1.1.0",
		          "requires_core_api": 3},
		"baton-tui": {"artifact": "bin/baton-tui", "version": "1.1.0",
		              "requires_core_api": 3},
	},
}


def live_pair(tmp_path, protocol_doc: bytes):
	"""A pair shaped like the one production RUNS: `bin/` and `dist/` only.

	Built rather than copied. The recovery suite used to copy the checkout's
	`bin/baton` and `bin/baton-tui`, and the Checkpoint A ruling is that those
	artifacts stay out of the repository — so there is nothing to copy, and
	relabelling the candidate's manifests does not work either: certification
	opens the archive and refuses a manifest whose `product_version` disagrees
	with the catalog the artifact carries. (It refused exactly that, which is
	the check working.)

	So these are REAL zipapps carrying a protocol-10 catalog at the version
	`recover_legacy.RECOVERABLE` names, with manifests that describe them and
	pin the caller's protocol document. `protocol_doc` must be the bytes of
	the MAINTAINED document, because recovery refuses a pair whose pinned
	document has moved on — that refusal is one of the properties under test.

	What this no longer exercises, said plainly: the historical 1.1.0 bytes.
	They are not in the repository. Every assertion downstream is about the
	relationship between an artifact and the manifest beside it, which is
	what recovery actually checks.
	"""
	global CATALOG
	source = tmp_path / "live"
	(source / "bin").mkdir(parents=True)
	(source / "dist").mkdir()

	original, CATALOG = CATALOG, LEGACY_CATALOG
	try:
		cli, cli_members = _zipapp({"__main__.py": b"# cli bootstrap\n"})
		tui, tui_members = _zipapp({"__main__.py": b"# console bootstrap\n",
		                            "baton_tui/__init__.py": b"# pretend console\n"})
	finally:
		CATALOG = original

	(source / "bin" / "baton").write_bytes(cli)
	(source / "bin" / "baton-tui").write_bytes(tui)
	core = {"version": "1.1.0", "api_version": 3,
	        "package_sha256": _core_digest(cli_members)}
	assert core["package_sha256"] == _core_digest(tui_members)
	common = {"protocol_version": 10, "requires_core_api": 3,
	          "embeds_core": core, "python_min": "3.11",
	          "sqlite_min": "3.37.0",
	          "protocol_doc": "docs/AGENTS-MAILBOX-PROTO.md",
	          "protocol_doc_sha256": _sha(protocol_doc)}
	(source / "dist" / "DISTRIBUTION.json").write_text(json.dumps({
		"tool": "baton", "artifact": "bin/baton", "artifact_sha256": _sha(cli),
		"product_version": "1.1.0",
		"source_sha256": _sha(cli_members["baton_core/_impl.py"]),
		**common}, indent=2))
	(source / "dist" / "DISTRIBUTION-TUI.json").write_text(json.dumps({
		"tool": "baton-tui", "artifact": "bin/baton-tui",
		"artifact_sha256": _sha(tui), "product_version": "1.1.0",
		"members": sorted(tui_members), **common}, indent=2))
	return source
