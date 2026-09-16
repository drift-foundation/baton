"""W183883 claim186890 — reversal probes for the real installed delivery.

What the first REAL installed run found, and what now holds it: frozen,
`bootstrap` computed its own "checkout" by walking three parents up from
`__file__` and so answered the INSTANCE DESTINATION -- refusing every repeated
install with "inside the checkout at <that same destination>"; and a composed
install told the operator to export the source-run operands it does not need.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186890")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE,
                ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

# The accepted stage fixtures read this repository's own evidence vectors by a
# path relative to the tree root, so the copy needs to see them. READ ONLY, and
# a link rather than a copy so nothing here can write into the dossier.
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"bootstrap": TREE / "python" / "tools" / "bootstrap.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

GATES = "tests.tools.test_instance.TheAdmissionDecidesBeforeAnythingHappens."
TELLS = "tests.tools.test_bootstrap.WhatItTELLSYouToDoNext."

INLINE = """    tree = checkout()
    resolved = os.path.realpath(destination)"""
WALKED = """    tree = os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    resolved = os.path.realpath(destination)"""

PROBES = [
    {"label": "Q1-frozen-the-checkout-is-computed-from-__file__-again",
     "file": "bootstrap",
     "before": INLINE,
     "after": WALKED,
     "checks": [GATES + "test_FROZEN_the_checkout_is_the_bundle_and_not_the_destination"],
     "intended": "inside the checkout"},
    {"label": "Q2-installing-is-told-to-export-the-source-run-operands",
     "file": "bootstrap",
     "before": "    if not installing:",
     "after": "    if True:",
     "checks": [TELLS + "test_installing_is_not"],
     "intended": "Now export these"},
    {"label": "Q3-the-source-run-form-stops-being-told-what-to-export",
     "file": "bootstrap",
     "before": "    if not installing:",
     "after": "    if False:",
     "checks": [TELLS + "test_running_from_the_checkout_is_told_what_to_export"],
     "intended": "Now export these"},
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
restored, restore_seconds = run(["tests.tools.test_instance",
                                 "tests.tools.test_bootstrap"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-186890.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
