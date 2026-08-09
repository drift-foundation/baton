"""Deterministic builder for the SEPARATE console trial artifact.

Produces `bin/baton-tui`: a self-contained zipapp of `baton_core` +
`baton_tui`, for Slawomir's human-acceptance trial.

Deliberately a second builder rather than an option on `build_zipapp.py`.
The agent CLI, its source, `bin/baton`, its builder and `DISTRIBUTION.json`
must stay BYTE-IDENTICAL during the trial, and the surest way to guarantee
that is for the code that builds them never to run. The two artifacts share
`baton_core` as source and share nothing else.

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

HERE = os.path.dirname(os.path.abspath(__file__))
FIXED_DATE = (2020, 1, 1, 0, 0, 0)

BOOTSTRAP = '''\
# Zipapp bootstrap. Kept parseable by old interpreters so the floor
# diagnostics are reachable rather than a SyntaxError. Exit code 2 is the
# documented environment-floor result, matching the CLI.
import sys

if sys.version_info < (3, 11):
    sys.stderr.write(
        "baton-tui: Python %d.%d is below the required 3.11 floor\\n"
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

PACKAGES = ("baton_core", "baton_tui")


def _members() -> list[tuple[str, bytes]]:
	members = [("__main__.py", BOOTSTRAP.encode("utf-8"))]
	for package in PACKAGES:
		directory = os.path.join(HERE, package)
		for name in sorted(os.listdir(directory)):
			if not name.endswith(".py"):
				continue
			with open(os.path.join(directory, name), "rb") as handle:
				members.append((f"{package}/{name}", handle.read()))
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

	sys.path.insert(0, HERE)
	import baton_core
	import baton_tui
	manifest = {
		"tool": "baton-tui",
		"tui_version": baton_tui.TUI_VERSION,
		"requires_core_api": baton_tui.REQUIRES_CORE_API,
		"core_api_version": baton_core.CORE_API_VERSION,
		"protocol_version": baton_core.PROTOCOL_VERSION,
		"python_min": "3.11",
		"artifact": "bin/baton-tui",
		"artifact_sha256": hashlib.sha256(payload).hexdigest(),
		"members": sorted(name for name, _ in members),
	}
	# A SEPARATE manifest: DISTRIBUTION.json belongs to the CLI and is not
	# touched during the trial.
	with open(os.path.join(root, "DISTRIBUTION-TUI.json"), "w") as handle:
		json.dump(manifest, handle, indent=2, sort_keys=True)
		handle.write("\n")
	return manifest


if __name__ == "__main__":
	out = sys.argv[1] if len(sys.argv) > 1 else HERE
	print(json.dumps(build(out), indent=2, sort_keys=True))
