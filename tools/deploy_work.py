#!/usr/bin/env python3
"""Deploy the v11 `baton-work` product into an EXPLICIT distribution root.

v11-ONLY, by the frozen-v10 ruling: this tool shares nothing with
`tools/deploy.py`, reads nothing from the v10 catalogs or release tree, and
never touches a v10 path. It exists so the Gate B handoff is a real install
command instead of hand-run zipapp steps.

The distribution model is WS-6's: an exact release directory is IMMUTABLE.
The target is an explicit path the operator names; it must not exist yet —
this tool never adopts, overwrites, or deletes. The layout is the ruled
release shape:

    <target>/bin/baton             executable zipapp (cli:entry)
    <target>/bin/acp-baton-bridge  the co-deployed generic ACP readiness
                                   client (W163 distribution ruling)
    <target>/lib/acp-baton-bridge/ its private runtime: source, pinned
                                   lockfile, README, acceptance suite,
                                   and node_modules RESOLVED DURING
                                   CANDIDATE CONSTRUCTION — the deployed
                                   release runs without the source
                                   checkout, npm, or network
    <target>/lib/codex-event-bridge/src/  the shared projection-5
                                   envelope gate the bridge imports, and
                                   the execution-policy generator the
                                   shipped dispatcher template names
    <target>/doc/BATON-WORK.md     the operator quickstart
    <target>/doc/AGENTS-MAILBOX-PROTO.md  the agent protocol contract
    <target>/conf/baton.example.json  a complete valid config example
    <target>/conf/infra.example.json  the strict repository lifecycle example
    <target>/conf/codex-event-bridge.template.json  its rendered dispatcher config
    <target>/conf/acp-{claude,gemini}.template.json  agent-specific ACP configs
    <target>/conf/acp-bridge.template.json  generic ACP configuration example
    <target>/conf/acp-bridge-*.example.json  non-secret bridge examples
                                   (explicit placeholders; cannot run
                                   as shipped)
    <target>/tmpl/<pattern>.md     the numbered template ASSETS beside bin/
                                   (M6: never embedded in the zipapp)

The candidate is staged in a scratch directory beside the target and
published with one atomic rename: the visible state is the complete
distribution or nothing.

Usage:  python3 tools/deploy_work.py /explicit/target/dir
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PACKAGE = os.path.join(REPO, "src", "baton_work")
SOURCE_TEMPLATES = os.path.join(REPO, "tmpl")
# The complete distribution beyond the executable: documentation and a
# configuration example ride every release as immutable assets.
SOURCE_ASSETS = (
	("docs/BATON-WORK.md", "doc/BATON-WORK.md"),
	("docs/BATON-SETUP.md", "doc/BATON-SETUP.md"),
	# W103: the agent protocol contract ships WITH the release, so a
	# participating team bootstraps its agent policy from the same exact
	# release as its CLI rather than from whatever the source checkout
	# happens to say today.
	("docs/AGENTS-MAILBOX-PROTO.md", "doc/AGENTS-MAILBOX-PROTO.md"),
	# W104: the operating guide ships for the same reason — a
	# participant learns how to work this release safely from
	# THIS release, not from a checkout they may not have.
	("docs/EFFECTIVE-BATON.md", "doc/EFFECTIVE-BATON.md"),
	("conf/baton.example.json", "conf/baton.example.json"),
	("conf/infra.example.json", "conf/infra.example.json"),
	# W459: the example manifest renders the dispatcher's configuration
	# from this template, so a release that shipped one without the
	# other would ship a manifest that cannot load.
	("conf/codex-event-bridge.template.json",
	 "conf/codex-event-bridge.template.json"),
	("conf/acp-bridge.template.json", "conf/acp-bridge.template.json"),
	("conf/acp-claude.template.json", "conf/acp-claude.template.json"),
	("conf/acp-gemini.template.json", "conf/acp-gemini.template.json"),
	# W163: non-secret bridge example configurations — every value an
	# explicit placeholder; nothing runnable as shipped.
	("examples/acp-bridge-claude.json",
	 "conf/acp-bridge-claude.example.json"),
	("examples/acp-bridge-gemini.json",
	 "conf/acp-bridge-gemini.example.json"),
)

# W163 (distribution ruling, 2026-08-17): the generic acp-baton-bridge
# co-deploys with Baton as a ready product. Its runtime dependencies are
# resolved INTO the candidate before atomic publication (a staged
# `npm ci` from the committed exact-version lockfile); a missing tool or
# failed resolution refuses the deployment before the target exists.
# Agent adapters, credentials, and prohibition policies remain
# deployment-owned and are never bundled.
SOURCE_BRIDGE = os.path.join(REPO, "tools", "acp-baton-bridge")
SOURCE_SHARED_GATE = (
	"tools/codex-event-bridge/src/codex_baton_bridge.mjs",
	"tools/codex-event-bridge/src/config.mjs",
	# finding-deployed-exec-policy-helper: the shipped dispatcher
	# template tells the operator to generate the exact execution-policy
	# rules with this module, and d46ab1e shipped that instruction
	# without the module — a standalone deployment could not follow its
	# own instructions and would leave somebody hand-authoring
	# security-sensitive rules. What ships is a BYTE-EQUAL IMMUTABLE
	# COPY of the reviewed source helper, pinned by the deployer test —
	# not the same filesystem artifact the dispatcher imports, because
	# the canonical dispatcher still runs from a source checkout
	# (`conf/infra.example.json`) and this release ships no
	# `bin/codex-event-bridge`. Byte parity is therefore the whole
	# guarantee: it is what keeps the rules an operator generates and
	# the rules a dispatcher audits from being produced by two
	# different implementations.
	"tools/codex-event-bridge/src/exec_policy.mjs",
	"tools/codex-event-bridge/src/role_instructions.mjs",
	# W93 slice 4: the ACP bridge imports the shared runtime-lease
	# publisher from the same directory it already takes the role
	# instructions from, so the deployed release carries it too. The
	# W163 no-checkout test is what catches a miss here — it did.
	"tools/codex-event-bridge/src/runtime_publisher.mjs",
	"tools/codex-event-bridge/src/send_event.mjs",
)
BRIDGE_WRAPPER = """#!/usr/bin/env bash
# Distribution entry point for the co-deployed generic ACP readiness
# client (W163). The runtime lives in ../lib/acp-baton-bridge with its
# dependencies already resolved; nothing is fetched or installed here.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec node "$HERE/../lib/acp-baton-bridge/src/acp_baton_bridge.mjs" "$@"
"""


# W4 (finding-v11-reproducible-zipapp): the executable is a REPRODUCIBLE
# artifact — its bytes depend only on its intentional source inputs.
#
# `zipapp.create_archive` stamps every member with its staging mtime, so
# two deployments of byte-identical sources differed. The observed
# evidence caught only generated `__main__.py`, because the copied
# sources kept their mtimes between the two builds in one checkout; a
# fresh clone or a touched file moves the other thirteen members too.
# The fix is therefore metadata-wide rather than a special case for the
# generated member.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)   # the earliest the DOS format holds
FILE_ATTR = (0o100644 << 16)
DIR_ATTR = (0o040755 << 16) | 0x10

# Byte-for-byte what zipapp writes, so the ruled bootstrap is unchanged:
# cli:entry, NOT cli:main — zipapp discards the target's return value,
# which turned refusals into exit 0 (the WF-06 lesson).
MAIN_SOURCE = ("# -*- coding: utf-8 -*-\n"
               "import baton_work.cli\n"
               "baton_work.cli.entry()\n")
SHEBANG = b"#!/usr/bin/env python3\n"


def _members(staging):
	"""Every archive member as (arcname, is_dir, bytes), in ONE sorted
	order. Walk order is filesystem-dependent — inode order on some
	filesystems — so enumeration is sorted rather than trusted."""
	out = [("__main__.py", False, MAIN_SOURCE.encode("utf-8"))]
	for base, dirs, files in os.walk(staging):
		dirs.sort()
		rel = os.path.relpath(base, staging)
		if rel != ".":
			out.append((rel.replace(os.sep, "/") + "/", True, b""))
		for name in sorted(files):
			path = os.path.join(base, name)
			arcname = os.path.relpath(path, staging).replace(os.sep, "/")
			with open(path, "rb") as handle:
				out.append((arcname, False, handle.read()))
	return sorted(out, key=lambda entry: entry[0])


def _write_zipapp(staging, archive):
	"""The deterministic writer: fixed member timestamps and modes, a
	pinned create_system, sorted members, and stored (uncompressed)
	entries — nothing derived from the build host or the clock."""
	with open(archive, "wb") as handle:
		handle.write(SHEBANG)
		with zipfile.ZipFile(handle, "w") as bundle:
			for arcname, is_dir, payload in _members(staging):
				info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
				# 3 = Unix. ZipInfo otherwise picks it from the BUILD
				# host, so the same sources would differ across hosts.
				info.create_system = 3
				info.external_attr = DIR_ATTR if is_dir else FILE_ATTR
				info.compress_type = zipfile.ZIP_STORED
				bundle.writestr(info, payload)
	os.chmod(archive, 0o755)


def _stage_bridge(scratch: str) -> None:
	"""Assemble the READY bridge product inside the candidate."""
	if not os.path.isdir(SOURCE_BRIDGE):
		fail(f"this checkout is incomplete: {SOURCE_BRIDGE} is missing")
	runtime = os.path.join(scratch, "lib", "acp-baton-bridge")
	shutil.copytree(SOURCE_BRIDGE, runtime,
	                ignore=shutil.ignore_patterns("node_modules"))
	for relative in SOURCE_SHARED_GATE:
		source = os.path.join(REPO, relative)
		if not os.path.isfile(source):
			fail(f"this checkout is incomplete: {source} is missing")
		destination = os.path.join(
			scratch, "lib", os.path.relpath(relative, "tools"))
		os.makedirs(os.path.dirname(destination), exist_ok=True)
		shutil.copyfile(source, destination)
	if shutil.which("node") is None or shutil.which("npm") is None:
		fail("node and npm (node >= 20) are required to assemble the "
		     "co-deployed ACP bridge; refusing before publication")
	resolved = subprocess.run(
		["npm", "ci", "--no-fund", "--no-audit"], cwd=runtime,
		capture_output=True, text=True)
	if resolved.returncode != 0:
		fail("npm ci could not resolve the bridge's pinned dependencies "
		     f"from its committed lockfile; refusing before "
		     f"publication: {resolved.stderr.strip()[:400]}")
	if not os.path.isdir(os.path.join(
			runtime, "node_modules", "@agentclientprotocol", "sdk")):
		fail("dependency resolution left no @agentclientprotocol/sdk; "
		     "refusing an incomplete bridge runtime before publication")
	wrapper = os.path.join(scratch, "bin", "acp-baton-bridge")
	with open(wrapper, "w", encoding="utf-8") as handle:
		handle.write(BRIDGE_WRAPPER)
	os.chmod(wrapper, 0o755)


def fail(message: str) -> "NoReturn":
	print(json.dumps({"error": message}), file=sys.stderr)
	raise SystemExit(1)


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	if len(argv) != 1 or argv[0].startswith("-"):
		fail("usage: deploy_work.py TARGET_DIR — the explicit v11 "
		     "distribution root to create; nothing is inferred and "
		     "nothing existing is touched")
	target = os.path.abspath(argv[0])
	if os.path.lexists(target):
		fail(f"{target} already exists; an exact release directory is "
		     f"immutable — deploy each release into a NEW explicit "
		     f"directory, never over an old one")
	parent = os.path.dirname(target)
	if not os.path.isdir(parent):
		fail(f"{parent} is not an existing directory; create the "
		     f"parent first — deploy writes only where you chose")
	if not os.path.isdir(SOURCE_PACKAGE) or \
			not os.path.isdir(SOURCE_TEMPLATES):
		fail(f"this checkout is incomplete: expected {SOURCE_PACKAGE} "
		     f"and {SOURCE_TEMPLATES}")

	scratch = tempfile.mkdtemp(prefix=".deploy-work-", dir=parent)
	try:
		staging = os.path.join(scratch, "app")
		# R111: candidate assembly carries INTENTIONAL sources only —
		# host-generated bytecode never becomes release content.
		shutil.copytree(SOURCE_PACKAGE,
		                os.path.join(staging, "baton_work"),
		                ignore=shutil.ignore_patterns(
		                    "__pycache__", "*.pyc", "*.pyo"))
		os.mkdir(os.path.join(scratch, "bin"))
		archive = os.path.join(scratch, "bin", "baton")
		_write_zipapp(staging, archive)
		shutil.rmtree(staging)
		templates = sorted(name for name in os.listdir(SOURCE_TEMPLATES)
		                   if name.endswith(".md"))
		if not templates:
			fail(f"{SOURCE_TEMPLATES} holds no numbered templates; "
			     f"refusing to publish an assetless distribution")
		os.mkdir(os.path.join(scratch, "tmpl"))
		for name in templates:
			shutil.copyfile(os.path.join(SOURCE_TEMPLATES, name),
			                os.path.join(scratch, "tmpl", name))
		for source_rel, target_rel in SOURCE_ASSETS:
			source = os.path.join(REPO, source_rel)
			if not os.path.isfile(source):
				fail(f"this checkout is incomplete: {source} is "
				     f"missing; refusing to publish a partial "
				     f"distribution")
			destination = os.path.join(scratch, target_rel)
			os.makedirs(os.path.dirname(destination), exist_ok=True)
			shutil.copyfile(source, destination)
		_stage_bridge(scratch)
		with open(archive, "rb") as handle:
			digest = hashlib.sha256(handle.read()).hexdigest()
		os.rename(scratch, target)
	except BaseException:
		shutil.rmtree(scratch, ignore_errors=True)
		raise
	print(json.dumps({
		"target": target,
		"executable": os.path.join(target, "bin", "baton"),
		"acp_bridge": os.path.join(target, "bin", "acp-baton-bridge"),
		"archive_sha256": digest,
		"templates": templates,
		"next": f"{os.path.join(target, 'bin', 'baton')} init "
		        f"YOUR_COORDINATION_HOME",
	}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
