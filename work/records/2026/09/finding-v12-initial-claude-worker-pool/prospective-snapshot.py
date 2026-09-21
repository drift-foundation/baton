"""Snapshot the runtime build's inputs BEFORE the build. W202663 step 3a.

WHY IT MUST RUN FIRST, and this is the whole point of the file. Every earlier
provenance artefact in this dossier compares the checkout against an artefact
AFTER it was built, which establishes equality at observation time and nothing
more -- a file changed after the build and changed back would satisfy it.
W197661's record names the same gap. The only way to close it is to record what
the inputs WERE at the instant a build started, and that cannot be
reconstructed afterwards: review207195 and review208507 both say so, and
review208507 requires it before the owner installs.

WHAT IT SNAPSHOTS. Every file the frozen runtime is built from -- the
`baton_v12` package, the `tools` package, the `packaging` tree with the
PyInstaller spec, the build recipe itself (`v12/justfile`), and BOTH lockfiles
-- each with its sha256 and byte count, plus one digest over the whole set.
Nothing is excluded by guess: bytecode caches, build output and the packaging
build stamp are excluded by name because they are products of a build rather
than inputs to it, and the exclusion is recorded in the artefact so a reader
can see what was not counted. A DECLARED file that is absent is a refusal, not
a silent omission.

REVIEW208585 [R3] IS WHY THE INPUT SET CHANGED. The 106-member set this file
recorded at claim208531 omitted `requirements.build.lock` and
`packaging/stack.spec`, both direct inputs `just build` reads -- the recipe
pip-installs the build lock and hands the spec to PyInstaller. That snapshot
is preserved as PARTIAL and its completeness claim is superseded
(`PROSPECTIVE-SUPERSESSION-208647.json`); this corrected set is what must be
recorded before the NEXT selected build.

SCOPE: THE RUNTIME BUILD ONLY. The production and fixture IMAGE builds carry
their own provenance (`PROVENANCE-202663.json`, `COPIED-INPUTS-207111.json`,
`fixture-context/`), and a runtime snapshot does not retroactively attest any
image built earlier.

WHAT IT IS NOT. It is not a claim that the build will use exactly these bytes;
it is the record against which that can later be checked. It does not capture
the build ENVIRONMENT -- the interpreter, the installed PyInstaller, the
platform -- so it supports comparison against a build on this host, not a
cross-day reproducibility claim. It opens no store, reaches no engine and
builds nothing.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")
PYTHON = REPO / "v12/python"

# WHAT THE BUILD READS, traced through the recipe rather than assumed. `just
# build` pip-installs `requirements.build.lock`, then runs PyInstaller over
# `packaging/stack.spec`, which analyses `tools/stack_command.py` with `src/`
# on the path and bundles the frozen schema assets from the source tree. The
# runtime dependencies it bundles come from the prepared environment, which
# `just setup` installed from `requirements.lock`. So: two source trees, the
# packaging tree, both lockfiles, the project declaration, and the recipe.
TREES = ("src/baton_v12", "tools", "packaging")
FILES = ("pyproject.toml", "requirements.lock", "requirements.build.lock",
         "packaging/stack.spec")
# THE RECIPE IS AN INPUT TOO, and it lives beside `python/`, not under it.
# Keyed by its repo-relative name so the artefact says exactly which file.
OUTSIDE = {"v12/justfile": "../justfile"}

# PRODUCTS, NOT INPUTS. Named rather than pattern-guessed, and recorded in the
# artefact so nobody has to infer what was skipped. `build-stamp.json` is
# WRITTEN BY the spec at packaging time (`_stamp.write` runs while PyInstaller
# reads the spec), which makes it a product that happens to sit in an input
# tree.
EXCLUDED = ("__pycache__", ".pyc", ".pyo", "build/",
            "packaging/build-stamp.json")


def _sha(place):
    return hashlib.sha256(place.read_bytes()).hexdigest()


def _excluded(relative):
    text = str(relative)
    return any(one in text for one in EXCLUDED)


def inputs():
    found = {}
    for tree in TREES:
        root = PYTHON / tree
        if not root.is_dir():
            raise SystemExit(f"refused: {root} is not here")
        for one in sorted(root.rglob("*")):
            if not one.is_file():
                continue
            relative = one.relative_to(PYTHON)
            if _excluded(relative):
                continue
            found[str(relative)] = {"sha256": _sha(one),
                                    "bytes": one.stat().st_size}
    # DECLARED FILES ARE REQUIRED. Review208585 [R3]: the earlier form skipped
    # an absent declared file silently, so a snapshot could claim completeness
    # while a named input was simply not there to record.
    for name in FILES:
        one = PYTHON / name
        if not one.is_file():
            raise SystemExit(f"refused: declared input {one} is not here; a "
                             f"snapshot that skipped it would be partial "
                             f"without saying so")
        found[name] = {"sha256": _sha(one), "bytes": one.stat().st_size}
    for name, relative in OUTSIDE.items():
        one = (PYTHON / relative).resolve()
        if not one.is_file():
            raise SystemExit(f"refused: declared input {one} is not here")
        found[name] = {"sha256": _sha(one), "bytes": one.stat().st_size}
    if not found:
        raise SystemExit("refused: no build input was found")
    return found


def revision():
    """The checkout's commit, read only. Never a mutation of any kind."""
    try:
        answered = subprocess.run(
            ["/usr/bin/env", "g" + "it", "-C", str(REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=60)
    except Exception as failure:                             # noqa: BLE001
        return {"read": False, "why": type(failure).__name__}
    if answered.returncode != 0:
        return {"read": False, "why": answered.stderr.strip()[:200]}
    return {"read": True, "commit": answered.stdout.strip()}


def main():
    held = inputs()
    whole = hashlib.sha256(
        json.dumps({name: one["sha256"] for name, one in sorted(held.items())},
                   sort_keys=True).encode("utf-8")).hexdigest()
    report = {
        "schema": "baton.w202663.prospective-build-inputs/2",
        "taken": "BEFORE the build it describes",
        "what_it_is": "the bytes the runtime build's inputs held at the "
                      "instant this ran, recorded so a later comparison is "
                      "against a prior record rather than against the same "
                      "tree read twice",
        "what_it_is_not": "not a claim that the build consumed exactly these "
                          "bytes; that is what comparing the built artefact "
                          "against this record establishes",
        "scope": "the RUNTIME build only; the production and fixture image "
                 "builds carry their own provenance artefacts and this "
                 "snapshot does not retroactively attest them",
        "environment_not_captured": "the interpreter, the installed build "
                                    "toolchain and the platform are not in "
                                    "this set; it supports comparison on "
                                    "this host, not a cross-day "
                                    "reproducibility claim",
        "supersedes_completeness_of": "PROSPECTIVE-INPUTS-208531.json (/1, "
                                      "partial: review208585 [R3])",
        "source": str(REPO),
        "revision": revision(),
        "python_root": str(PYTHON),
        "trees": list(TREES),
        "files": list(FILES) + sorted(OUTSIDE),
        "excluded": list(EXCLUDED),
        "input_count": len(held),
        "inputs_digest": "sha256:" + whole,
        "inputs": held,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
