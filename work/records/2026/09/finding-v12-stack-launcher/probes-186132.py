"""W183883 claim186132 reversal probes for the `just test-bootstrap` wrapper.

Every probe must FAIL. A probe that passes proves the guard is held by no
check, which is a test gap or a redundant guard -- not a result.
"""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
J = TREE / "justfile"
PRISTINE = J.read_text()

PROBES = [
 ("the-recipe-uses-the-ambient-interpreter",
  '''	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}" PYTHONPATH=src:. \\
		timeout --kill-after=10s 180s \\
		"$PREPARED" -m unittest -v tests.tools.test_bootstrap''',
  '''	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}" PYTHONPATH=src:. \\
		timeout --kill-after=10s 180s \\
		python3 -m unittest -v tests.tools.test_bootstrap''',
  ["TheRecipesUseIt.test_every_stack_recipe_resolves_the_prepared_interpreter"]),

 ("the-recipe-installs-on-the-way-through",
  '''	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}"''',
  '''	python3 -m tools.environment setup
	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}"''',
  ["TheRecipesUseIt.test_no_stack_recipe_installs_anything"]),

 ("the-run-is-unbounded",
  '''		timeout --kill-after=10s 180s \\
		"$PREPARED" -m unittest -v tests.tools.test_bootstrap''',
  '''		"$PREPARED" -m unittest -v tests.tools.test_bootstrap''',
  ["TheRecipesUseIt.test_the_bootstrap_test_recipe_carries_the_reviewed_bounds"]),

 ("a-failing-suite-is-swallowed",
  '''	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}" PYTHONPATH=src:. \\
		timeout --kill-after=10s 180s \\
		"$PREPARED" -m unittest -v tests.tools.test_bootstrap''',
  '''	env BATON_V12_STACK_TEST_ROOT="{{ROOT}}" PYTHONPATH=src:. \\
		timeout --kill-after=10s 180s \\
		"$PREPARED" -m unittest -v tests.tools.test_bootstrap || true''',
  ["TheRecipesUseIt.test_the_bootstrap_test_recipe_cannot_swallow_a_failure"]),

 ("the-root-is-not-forwarded",
  '''	exec env BATON_V12_STACK_TEST_ROOT="{{ROOT}}" PYTHONPATH=src:. \\''',
  '''	exec env PYTHONPATH=src:. \\''',
  ["TheInterpreterOverrideIsExecutable.test_the_bootstrap_test_root_defaults_to_a_disk_backed_place",
   "TheInterpreterOverrideIsExecutable.test_a_named_bootstrap_test_root_reaches_the_environment",
   "TheRecipesUseIt.test_the_bootstrap_test_recipe_carries_the_reviewed_bounds"]),

 ("the-root-defaults-into-a-memory-filesystem",
  '''test-bootstrap ROOT="/var/tmp":''',
  '''test-bootstrap ROOT="/tmp":''',
  ["TheInterpreterOverrideIsExecutable.test_the_bootstrap_test_root_defaults_to_a_disk_backed_place"]),
]


def restore():
    J.write_text(PRISTINE)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"]
        + ["tests.tools.test_environment." + one for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, before, after, names in PROBES:
    restore()
    text = J.read_text()
    assert before in text, "probe %s does not apply" % label
    J.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(names)
    spent += seconds
    results.append({"probe": label, "checks": names, "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-48s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
done, seconds = run(["WhereItLives", "WhatItSeesThere", "NamingTheInterpreter",
                     "PreparingIt", "TheRecipesUseIt",
                     "TheInterpreterOverrideIsExecutable",
                     "AnInterruptedSetupResumes"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
