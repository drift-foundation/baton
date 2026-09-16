"""W183883 claim187015 — reversal probes for the recipe gaps and the repository verb.

Review 2026-09-16T14-06-35Z found two recipe gaps -- an optional operand
resolved unconditionally, so the form that installs nothing died in the shell;
and a gate that inherited its own target and could pass while skipping -- and
asked for the repository binding and a read-only verification.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-187015")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"justfile": TREE / "justfile",
         "bootstrap": TREE / "python" / "tools" / "bootstrap.py",
         "stack": TREE / "python" / "tools" / "stack.py",
         "packaging": TREE / "python" / "tests" / "tools" / "test_packaging.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

RECIPES = "tests.tools.test_environment.TheBootstrapRecipeReachesTheHelper."
GATE = "tests.tools.test_environment.TheGateCannotSkip."
REPO = "tests.tools.test_stack.WhatTheRepositoryIS."
BOUND = "tests.tools.test_instance.TheDestinationOwnsItsWorkspace."

PROBES = [
    {"label": "S1-the-optional-distro-is-resolved-unconditionally-again",
     "file": "justfile",
     "before": '\tDISTRO_HERE="{{DISTRO}}"\n\tif [[ -n "{{DISTRO}}" ]]; then DISTRO_HERE="$(realpath -m "{{DISTRO}}")"; fi',
     "after": '\tDISTRO_HERE="$(realpath -m "{{DISTRO}}")"',
     "checks": [RECIPES + "test_the_form_that_installs_NOTHING_reaches_the_helper"],
     "intended": "not found in"},
    {"label": "S2-the-gate-stops-binding-the-bundle-it-just-built",
     "file": "justfile",
     "before": '\t\tBATON_V12_STACK_DISTRO="$PWD/build/out/distro" \\\n',
     "after": "",
     "checks": [GATE + "test_the_recipe_binds_the_bundle_it_just_built"],
     "intended": "not found in"},
    {"label": "S3-the-gate-skips-instead-of-failing",
     "file": "packaging",
     "before": "            if os.environ.get(REQUIRED):",
     "after": "            if False:",
     "checks": [GATE + "test_the_module_FAILS_rather_than_skipping_when_it_is_the_gate"],
     "intended": "AssertionError"},
    {"label": "S4-the-destination-stops-owning-its-workspace",
     "file": "bootstrap",
     # The DERIVATION is what is reverted, not the branch: reverting the
     # branch falls through to a KeyError, and an error is not the assertion
     # this is about [J1].
     "before": '        return dict(document, integration_workspace=places["repository"])',
     "after": "        return document",
     "checks": [BOUND + "test_an_absent_workspace_is_DERIVED_from_the_destination"],
     "intended": "AssertionError"},
    {"label": "S5-a-workspace-outside-the-destination-is-accepted",
     "file": "bootstrap",
     "before": "        if held != inside and not held.startswith(",
     "after": "        if False and held.startswith(",
     "checks": [BOUND + "test_a_workspace_OUTSIDE_the_destination_is_refused",
                BOUND + "test_a_LINK_out_of_the_destination_is_refused_too"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "S6-the-repository-report-believes-the-configuration",
     "file": "stack",
     "before": "    if not os.path.exists(named):",
     "after": "    if False:",
     "checks": [REPO + "test_an_absent_target_is_named_as_absent"],
     "intended": "AssertionError"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def restore():
    for place, text in PRISTINE.items():
        place.write_text(text)
    caches()


def target_of(probe):
    return FILES[probe["file"]]


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:.",
                 BATON_V12_STACK_TEST_ROOT="/var/tmp"))
    return done, time.monotonic() - started


results, spent = [], 0.0
for probe in PROBES:
    restore()
    target = target_of(probe)
    baseline, base_seconds = run(probe["checks"])
    spent += base_seconds
    text = target.read_text()
    assert probe["before"] in text, probe["label"]
    target.write_text(text.replace(probe["before"], probe["after"], 1))
    caches()
    reverted, seconds = run(probe["checks"])
    spent += seconds
    restore()
    said = reverted.stderr
    # THE FAILURE IS THE INTENDED ONE, not any error at all [J1]: an import
    # error or a misnamed check also exits non-zero and proves nothing.
    intended = ("AssertionError" in said and probe["intended"] in said
                and "Error: " not in said.split("AssertionError")[0][-40:])
    killed = (baseline.returncode == 0 and reverted.returncode != 0 and intended)
    results.append({
        "probe": probe["label"], "checks": probe["checks"],
        "baseline_passes_on_pristine": baseline.returncode == 0,
        "reverted_returncode": reverted.returncode,
        "failed_on_the_intended_assertion": intended,
        "valid_kill": killed,
        "seconds": round(base_seconds + seconds, 3)})
    if not killed:
        print("---- stderr tail, " + probe["label"] + " ----")
        print(said[-900:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.tools.test_environment",
                                 "tests.tools.test_stack",
                                 "tests.tools.test_instance"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-187015.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
