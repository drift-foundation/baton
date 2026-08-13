"""The candidate distribution the gates examine: `build/`, never the checkout.

`just build` prepares a complete candidate under `build/` and leaves the
repository's own `bin/` and `dist/` alone — a successful build used to replace
the executables live consumers were running, which made the build itself the
cutover and left `just deploy` guarding a door everyone had already walked
through.

So the packaged, currency and deterministic-build gates read from here.

THIS DOES NOT BUILD ANYTHING. SUPERSEDED: an earlier `ensure()` built the
candidate on demand, so that `pytest` would work on a fresh clone without
anyone having remembered `just build`. That collapsed the ruled sequence —

    just build
    just test
    just deploy DESTINATION

— back into one step: `just test` was no longer a check OF the candidate the
preceding build produced, it was free to replace that candidate with one of
its own. A gate that manufactures the artifact it claims to inspect reports on
bytes nobody chose to release.

Its freshness rule was the second half of the same mistake: comparing mtimes
decides what to test by timestamp, and timestamps are preserved by copies,
coarse on some filesystems, and older than the source after any checkout.
Staleness is settled instead by rebuilding deterministically and comparing
bytes — `test_release_version.py` does exactly that, and it answers with the
content rather than with the clock.

A missing candidate is therefore a legible refusal naming the step that was
skipped, and never a build.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import sys
import types

REPO = pathlib.Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(REPO / "src"))

import build_release                                   # noqa: E402
import deploy                                         # noqa: E402

ROOT = pathlib.Path(build_release.CANDIDATE)
CLI = ROOT / "bin" / "baton"
TUI = ROOT / "bin" / "baton-tui"
DIST = ROOT / "dist"

# What a complete candidate holds, as far as the gates are concerned. The
# manifests are here as well as the executables because a gate reading a
# manifest with no artifact beside it would report a shape, not a release.
ARTIFACTS = (CLI, TUI, DIST / "DISTRIBUTION.json", DIST / "DISTRIBUTION-TUI.json")


class MissingCandidate(Exception):
	"""There is nothing at `build/` to examine, and this is not the thing that
	makes one."""


def require() -> types.SimpleNamespace:
	"""The candidate, or a refusal naming the step that was skipped.

	SUPERSEDED: this used to ask whether four pathnames existed. Four
	placeholder files passed it — no payload, no release notes, no ownership
	record — and the public test run could then begin against a tree the
	deployer would refuse at the end of it. "Publication is atomic, so
	existence is enough" was an argument about how candidates are WRITTEN; it
	says nothing about what is at that path now.

	So this asks the two questions that decide it, through the SAME code the
	build and the deployer use rather than a third list that can drift:

	    build_release.validate  -- is this a candidate a build produced, byte
	                               for byte, with nothing added or missing?
	    deploy.certified        -- is it a set that could be deployed?

	It reads. It builds nothing and writes nothing.
	"""
	# `relpath` rather than `relative_to`: a candidate somewhere else entirely
	# is a legitimate thing to ask about, and naming it must not itself raise.
	missing = [os.path.relpath(path, REPO) for path in ARTIFACTS
	           if not path.exists()]
	if missing:
		raise MissingCandidate(
			f"no release candidate at {ROOT} ({', '.join(missing)} absent). "
			f"Run `just build` first: these gates examine the candidate a build "
			f"produced, and building one here would make them examine their own "
			f"output instead.")
	try:
		build_release.validate(str(ROOT))
	except build_release.BuildError as refusal:
		raise MissingCandidate(
			f"the tree at {ROOT} is not a candidate a build produced: {refusal} "
			f"Run `just build`.") from None
	try:
		deploy.certified(str(ROOT))
	except deploy.DeployError as refusal:
		raise MissingCandidate(
			f"the candidate at {ROOT} would not deploy: {refusal} "
			f"Run `just build`.") from None
	return types.SimpleNamespace(root=ROOT, cli=CLI, tui=TUI, dist=DIST)


def digest(path) -> str:
	return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main(argv=None) -> int:
	"""The preflight `just test` runs before it starts pytest.

	ONE refusal, before collection, rather than one per candidate-dependent
	area discovered part-way through a run. It only asks `require()`, so the
	recipe and the fixtures answer the same question the same way, and there is
	no second list of artifacts to drift.

	It reads. It builds nothing and writes nothing -- that is the whole point
	of moving the check here rather than restoring `ensure()`.
	"""
	try:
		found = require()
	except MissingCandidate as refusal:
		print(f"error: {refusal}", file=sys.stderr)
		return 1
	print(f"candidate: {found.root}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
