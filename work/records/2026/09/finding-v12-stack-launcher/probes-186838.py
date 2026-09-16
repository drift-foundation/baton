"""W183883 claim186838 — reversal probes for verify-before-execute.

Review 2026-09-16T13-36-58Z [K2]: the recipe helper answered from the SELECTOR
alone, so `just status <instance>` executed a changed launcher and returned
zero. A runtime cannot check its own bytes once it has been loaded.

Every probe proves a PASSING BASELINE on pristine code first [J1], and the
recipe probes run the ACTUAL recipe rather than its dry-run text -- the
expansion was right and what it ran was wrong, which is exactly what expansion
checks cannot see.

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186838")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE,
                ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

FILES = {
    "instance": TREE / "python" / "tools" / "instance.py",
    "justfile": TREE / "justfile",
}
PRISTINE = {place: place.read_text() for place in FILES.values()}

RECIPES = "tests.tools.test_environment.TheRecipesRefuseAChangedRuntime."
HELPER = "tests.tools.test_instance.WhatARecipeAsksAnInstance."

PROBES = [
    {"label": "P1-the-helper-answers-from-the-selector-alone-again",
     "file": "instance",
     "before": '        if taken.question == "command":',
     "after": "        if False:",
     "checks": [HELPER + "test_a_CHANGED_LAUNCHER_is_never_handed_back_to_be_run",
                HELPER + "test_a_CHANGED_LIBRARY_beside_it_is_refused_too",
                HELPER + "test_an_UNBOUND_EXTRA_file_in_the_bundle_is_refused"],
     # Reverted, the helper ANSWERS -- so the intended failure is the exit
     # that was 0 and the path that was printed, not a message.
     "intended": "!= (2, '')"},
    {"label": "P2-the-ACTUAL-recipe-runs-a-changed-runtime",
     "file": "instance",
     "before": '        if taken.question == "command":',
     "after": "        if False:",
     "checks": [RECIPES + "test_a_changed_launcher_never_executes",
                RECIPES + "test_a_changed_library_never_executes",
                RECIPES + "test_an_unbound_extra_resource_never_executes"],
     # Reverted, `just` exits 0: the recipe ran it. The stronger assertion
     # (the marker never appearing) is the one behind it.
     "intended": "ran it anyway"},
    {"label": "P3-the-places-an-operator-looks-are-refused-too",
     "file": "instance",
     "before": '        if taken.question == "command":',
     "after": '        if taken.question in ANSWERS:',
     "checks": [HELPER + "test_the_places_an_operator_LOOKS_are_still_answered"],
     "intended": "AssertionError"},
    {"label": "P4-the-recipe-stops-running-the-deployment-s-own-command",
     "file": "justfile",
     "before": '\t\texec "$INSTALLED" status --instance "{{INSTANCE}}"',
     "after": '\t\ttrue',
     "checks": [RECIPES + "test_an_unchanged_runtime_is_reached"],
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
        env=dict(os.environ, PYTHONPATH="src:."))
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
                                 "tests.tools.test_instance"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-186838.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
