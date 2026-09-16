"""W183883 claim187142 — the one product guard this claim added.

Review 2026-09-16T14-26-38Z: the operator packet left the derived workspace an
empty directory, and `reconciliation._prove_isolation` resolves the workspace's
OWN repository identity before anything is written. The deployment now says so
itself, and this asks whether that is held.

The rest of this claim is documentation, evidence and a harness; those are
checked by running them, not by reverting a guard, and this file does not
pretend otherwise.

Every probe proves a PASSING BASELINE on pristine code first [J1].
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-187142")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"stack": TREE / "python" / "tools" / "stack.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

REPO = "tests.tools.test_stack.WhatTheRepositoryIS."

PROBES = [
    {"label": "T1-an-empty-workspace-is-reported-without-what-it-costs",
     "file": "stack",
     "before": '    if "a repository" not in workspace:',
     "after": "    if False:",
     "checks": [REPO + "test_a_workspace_that_is_not_a_repository_says_what_that_costs"],
     "intended": "not found in"},
    {"label": "T2-every-workspace-is-told-it-is-not-a-repository",
     "file": "stack",
     "before": '    if "a repository" not in workspace:',
     "after": "    if True:",
     "checks": [REPO + "test_a_workspace_that_IS_a_repository_says_nothing_of_the_kind"],
     "intended": "unexpectedly found in"},
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
restored, restore_seconds = run(["tests.tools.test_stack"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-187142.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
