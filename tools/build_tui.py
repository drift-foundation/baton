"""Deterministic builder for the SEPARATE console trial artifact.

Produces `bin/baton-tui`: a self-contained zipapp of `baton_core` +
`baton_tui`, for Slawomir's human-acceptance trial.

Deliberately a second builder rather than an option on `build_zipapp.py`.
The agent CLI, its source, `bin/baton`, its builder and `DISTRIBUTION.json`
must stay BYTE-IDENTICAL during the trial, and the surest way to guarantee
that is for the CLI's `build()` never to run from here. What the two builders
DO share, deliberately, is the definition of the embedded core: `core_members`
and `attest_core` live in the CLI builder and are imported, so both artifacts
package the same members and attest them the same way. Sharing that is the
point -- two independent answers to "what is the core" is exactly the drift
the embedded-core attestation exists to detect.

Same determinism rules as the CLI builder: fixed timestamps, sorted entries,
stored (not deflated), no compiled artifacts — so the same inputs yield the
same sha256.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import sys
import zipfile

# See `build_zipapp.py`: explicit source layout rather than "this file's own
# directory is also the source root".
HERE = os.path.dirname(os.path.abspath(__file__))          # tools/
ROOT = os.path.dirname(HERE)                                # repository root
SRC = os.path.join(ROOT, "src")
FIXED_DATE = (2020, 1, 1, 0, 0, 0)

sys.path.insert(0, HERE)
# IMPORTED, never invoked: `core_members` and `attest_core` are the shared
# definition of what the embedded core IS. Importing this module builds
# nothing -- `build_zipapp.build()` is what writes the CLI, and this file
# never calls it.
import build_zipapp                        # noqa: E402  (sibling tool, not a package)

BOOTSTRAP = '''\
# Zipapp bootstrap. Kept parseable by old interpreters so the floor
# diagnostics are reachable rather than a SyntaxError. Exit code 2 is the
# documented environment-floor result, matching the CLI.
import sys

if sys.version_info < ({floor_tuple}):
    sys.stderr.write(
        "baton-tui: Python %d.%d is below the required {floor_text} floor\\n"
        % (sys.version_info[0], sys.version_info[1]))
    sys.exit(2)

try:
    import sqlite3  # noqa: F401
except ImportError:
    sys.stderr.write("baton-tui: the Python sqlite3 module is unavailable\\n")
    sys.exit(2)

try:
    import curses  # noqa: F401
except ImportError:
    sys.stderr.write(
        "baton-tui: the Python curses module is unavailable; the console "
        "needs a terminal library that the agent CLI does not\\n")
    sys.exit(2)

from baton_tui.driver import main

sys.exit(main())
'''



def _members() -> list[tuple[str, bytes]]:
	"""The console archive: its own package, plus the core it embeds.

	The core half comes from `build_zipapp.core_members()` rather than being
	walked again here. Two builders each deciding what "the core" contains is
	how one product ships a member the other does not, and the whole point of
	the embedded-core attestation is that the answer is the same object."""
	members = [("__main__.py", build_zipapp.bootstrap(BOOTSTRAP).encode("utf-8"))]
	members.extend(build_zipapp.core_members())
	tui_dir = os.path.join(SRC, "baton_tui")
	for name in sorted(os.listdir(tui_dir)):
		if not name.endswith(".py"):
			continue
		with open(os.path.join(tui_dir, name), "rb") as handle:
			members.append((f"baton_tui/{name}", handle.read()))
	return members


def build(root: str) -> dict:
	members = _members()
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
	target = os.path.join(bin_dir, "baton-tui")
	with open(target, "wb") as handle:
		handle.write(payload)
	os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	# THE SAME PROTOCOL DOCUMENT the CLI ships and pins. The console's manifest
	# used to omit it, so `certified()` checked the document for one product
	# and not the other -- an asymmetry with no argument behind it, found while
	# revalidating for independent versions.
	proto_name = os.path.join("docs", "AGENTS-MAILBOX-PROTO.md")
	canonical = os.path.join(ROOT, proto_name)
	with open(canonical, "rb") as handle:
		proto = handle.read()
	proto_target = os.path.join(root, proto_name)
	if os.path.abspath(proto_target) != os.path.abspath(canonical):
		os.makedirs(os.path.dirname(proto_target), exist_ok=True)
		with open(proto_target, "wb") as handle:
			handle.write(proto)

	catalog = build_zipapp._catalog()
	product = catalog.product("baton-tui")
	# DERIVED, like the CLI's. The console carries its OWN product version now
	# -- it is no longer "same key, same value as the CLI manifest: one
	# release, one number" -- and it attests to the exact core inside it.
	manifest = {
		"tool": "baton-tui",
		"product_version": product["version"],
		"requires_core_api": product["requires_core_api"],
		"embeds_core": build_zipapp.attest_core(members),
		"protocol_version": catalog.PROTOCOL_VERSION,
		"python_min": catalog.PYTHON_MIN,
		"sqlite_min": catalog.SQLITE_MIN_TEXT,
		"artifact": product["artifact"],
		"artifact_sha256": hashlib.sha256(payload).hexdigest(),
		"protocol_doc": proto_name,
		"protocol_doc_sha256": hashlib.sha256(proto).hexdigest(),
		"members": sorted(name for name, _ in members),
	}
	# A SEPARATE manifest: DISTRIBUTION.json belongs to the CLI and is not
	# touched during the trial.
	manifest_path = os.path.join(root, "dist", "DISTRIBUTION-TUI.json")
	os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
	with open(manifest_path, "w") as handle:
		json.dump(manifest, handle, indent=2, sort_keys=True)
		handle.write("\n")
	return manifest


if __name__ == "__main__":
	out = sys.argv[1] if len(sys.argv) > 1 else ROOT
	print(json.dumps(build(out), indent=2, sort_keys=True))
