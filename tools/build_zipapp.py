"""Deterministic stdlib-only zipapp builder for the baton tool.

Produces bin/baton — a self-contained executable Python archive whose bytes
depend only on the packaged sources (fixed timestamps, sorted entries, no
compiled artifacts), so rebuilding from the same inputs yields the same
sha256. Writes `dist/DISTRIBUTION.json` under the same root with the
version/floor manifest.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import sys
import zipfile

# EXPLICIT source layout, rather than "wherever this file happens to sit".
# The builder used to assume its own directory was also the repository root
# and the source root, which is precisely the working-directory dependence the
# layout refactor removes.
HERE = os.path.dirname(os.path.abspath(__file__))          # tools/
ROOT = os.path.dirname(HERE)                                # repository root
SRC = os.path.join(ROOT, "src")
FIXED_DATE = (2020, 1, 1, 0, 0, 0)  # deterministic member timestamp

BOOTSTRAP = '''\
# Zipapp bootstrap. This file must PARSE on old interpreters (syntax kept to
# ~Python 3.6) so the floor diagnostics below are reachable instead of a
# SyntaxError. Exit code 2 is the documented environment-floor result.
import sys

if sys.version_info < (3, 11):
    sys.stderr.write(
        "baton: Python %d.%d is below the required 3.11 floor\\n"
        % (sys.version_info[0], sys.version_info[1]))
    sys.exit(2)

try:
    import sqlite3  # noqa: F401
except ImportError:
    sys.stderr.write("baton: the Python sqlite3 module is unavailable\\n")
    sys.exit(2)

from baton_core.cli import main

sys.exit(main())
'''


def build(root: str) -> dict:
	"""ONE distribution-root contract: `root` receives the executable at
	`bin/baton`, its manifest at `dist/DISTRIBUTION.json`, and the protocol
	document at `docs/`. Every path the manifest records is relative to
	`root`, so a distribution root is self-contained -- which is the property
	that broke when the document was recorded without being copied."""
	# The CLI is built from `baton_core` now. `baton_v6.py` is NOT packaged
	# and is not imported by anything shipped: it stays in the tree as the
	# frozen differential ORACLE, which is the instrument parity is measured
	# with. Packaging it here would put the measurement inside the thing being
	# measured.
	source_path = os.path.join(SRC, "baton_core", "_impl.py")
	with open(source_path, "rb") as handle:
		source = handle.read()
	members = [("__main__.py", BOOTSTRAP.encode("utf-8"))]
	core_dir = os.path.join(SRC, "baton_core")
	for name in sorted(os.listdir(core_dir)):
		if not name.endswith(".py"):
			continue
		with open(os.path.join(core_dir, name), "rb") as handle:
			members.append((f"baton_core/{name}", handle.read()))
	buffer = io.BytesIO()
	buffer.write(b"#!/usr/bin/env python3\n")
	with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
		for name, data in sorted(members):
			info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
			info.external_attr = 0o644 << 16
			archive.writestr(info, data)
	payload = buffer.getvalue()
	bin_dir = os.path.join(root, "bin")
	os.makedirs(bin_dir, exist_ok=True)
	target = os.path.join(bin_dir, "baton")
	with open(target, "wb") as handle:
		handle.write(payload)
	os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	# A complete deployment ships the generic protocol document inside the
	# executable; the manifest records and pins it.
	# THE DISTRIBUTION ROOT IS SELF-CONTAINED. Every path the manifest records
	# resolves from the root the manifest sits in -- that is the contract, and
	# it predates the layout refactor.
	#
	# So the canonical document is COPIED into an alternate root, and is not
	# copied when building in place: there the target IS the canonical file,
	# and writing it would either be a no-op or a duplicate of the repository's
	# only protocol document.
	#
	# An earlier version of this refactor recorded the path without ever
	# copying it. Building into a scratch root then produced a manifest naming
	# a document that root did not contain, and the regression missed it
	# because I had resolved the built manifest's path against the SOURCE
	# repository -- where it always exists.
	proto_name = os.path.join("docs", "AGENTS-MAILBOX-PROTO.md")
	canonical = os.path.join(ROOT, proto_name)
	with open(canonical, "rb") as handle:
		proto = handle.read()
	proto_target = os.path.join(root, proto_name)
	if os.path.abspath(proto_target) != os.path.abspath(canonical):
		os.makedirs(os.path.dirname(proto_target), exist_ok=True)
		with open(proto_target, "wb") as handle:
			handle.write(proto)

	sys.path.insert(0, SRC)
	import baton_core
	# `source_sha256` keeps its meaning -- the hash of the implementation
	# source -- and that source is now `baton_core/_impl.py` rather than
	# `baton_v6.py`. The field is not redefined to cover the whole archive:
	# `artifact_sha256` already pins every packaged byte, and two fields
	# saying the same thing is how they stop agreeing.
	manifest = {
		"tool": "baton",
		"tool_version": baton_core.TOOL_VERSION,
		"protocol_version": baton_core.PROTOCOL_VERSION,
		"python_min": "3.11",
		"sqlite_min": ".".join(map(str, baton_core._impl.SQLITE_MIN)),
		"artifact": "bin/baton",
		"artifact_sha256": hashlib.sha256(payload).hexdigest(),
		"source_sha256": hashlib.sha256(source).hexdigest(),
		"protocol_doc": proto_name,
		"protocol_doc_sha256": hashlib.sha256(proto).hexdigest(),
	}
	manifest_path = os.path.join(root, "dist", "DISTRIBUTION.json")
	os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
	with open(manifest_path, "w") as handle:
		json.dump(manifest, handle, indent=2, sort_keys=True)
		handle.write("\n")
	return manifest


if __name__ == "__main__":
	out = sys.argv[1] if len(sys.argv) > 1 else ROOT
	print(json.dumps(build(out), indent=2, sort_keys=True))
