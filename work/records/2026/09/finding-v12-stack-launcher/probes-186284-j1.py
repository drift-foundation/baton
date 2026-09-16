"""W183883 claim186284 — the J1 replacement probe, with a BASELINE.

Review 2026-09-16T12-04-20Z [J1]: the superseded probe named
`TheRecipesUseIt.test_the_recipe_asks_the_helper_for_the_root_rather_than_assigning_one`
and that method belongs to `TheInterpreterOverrideIsExecutable`, so it errored
with AttributeError on the PRISTINE candidate. My harness only asked whether the
exit was non-zero, so an error counted as a mutation kill. It was not one.

THE METHODOLOGY IS FIXED HERE, not just the name: every probe now proves its
named checks PASS on pristine code first. A probe that cannot pass before the
reversal is not measuring the reversal.
"""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
J = TREE / "justfile"
PRISTINE = J.read_text()

LABEL = "I1-the-recipe-assigns-its-own-root-again"
BEFORE = '''	SELECTED="$(python3 -m tools.environment test-root --chosen "{{ROOT}}")"'''
AFTER = '''	SELECTED="{{ROOT}}"'''
CHECKS = ["TheInterpreterOverrideIsExecutable"
          ".test_the_recipe_asks_the_helper_for_the_root_rather_than_assigning_one"]


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"]
        + ["tests.tools.test_environment." + one for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


J.write_text(PRISTINE)
caches()
baseline, base_seconds = run(CHECKS)
print("baseline on pristine code:",
      "PASSES" if baseline.returncode == 0 else "DOES NOT PASS -- the probe is invalid")
assert baseline.returncode == 0, baseline.stderr[-800:]

text = J.read_text()
assert BEFORE in text
J.write_text(text.replace(BEFORE, AFTER, 1))
caches()
reverted, seconds = run(CHECKS)
J.write_text(PRISTINE)
caches()

# AND THE FAILURE IS THE INTENDED ASSERTION, not any error at all.
intended = "AssertionError" in reverted.stderr and "test-root --chosen" in reverted.stderr
print("reversed:", "FAILED (required)" if reverted.returncode else "PASSED -- PROVES NOTHING")
print("failed on the intended assertion:", intended)

restored, restore_seconds = run(CHECKS)
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probe": LABEL, "checks": CHECKS,
     "baseline_passes_on_pristine": baseline.returncode == 0,
     "baseline_seconds": round(base_seconds, 3),
     "reverted_returncode": reverted.returncode,
     "failed_as_required": reverted.returncode != 0 and intended,
     "failed_on_the_intended_assertion": intended,
     "seconds": round(seconds, 3),
     "restored_ok": restored.returncode == 0,
     "total_seconds": round(base_seconds + seconds + restore_seconds, 3)},
    indent=2, sort_keys=True))
print("valid kill:", reverted.returncode != 0 and intended)
