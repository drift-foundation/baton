"""W183883 claim186214 reversal probes for I1. Every probe must FAIL."""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
E = TREE / "python" / "tools" / "environment.py"
S = TREE / "python" / "tests" / "tools" / "test_stack.py"
J = TREE / "justfile"
PRISTINE = {E: E.read_text(), S: S.read_text(), J: J.read_text()}

PROBES = [
 ("I1-the-default-is-assigned-over-an-exported-root", E, "environment",
  '''    selected = (chosen or "").strip() or environ.get(TEST_ROOT_ENV, "").strip() \\
        or DEFAULT_TEST_ROOT''',
  '''    selected = (chosen or "").strip() or DEFAULT_TEST_ROOT''',
  ["TheBootstrapTestRootFollowsTheOperator.test_an_exported_selection_beats_the_default"]),

 ("I1-an-exported-root-beats-an-explicit-operand", E, "environment",
  '''    selected = (chosen or "").strip() or environ.get(TEST_ROOT_ENV, "").strip() \\
        or DEFAULT_TEST_ROOT''',
  '''    selected = environ.get(TEST_ROOT_ENV, "").strip() or (chosen or "").strip() \\
        or DEFAULT_TEST_ROOT''',
  ["TheBootstrapTestRootFollowsTheOperator.test_an_explicit_operand_beats_an_exported_selection"]),

 ("I1-an-empty-operand-counts-as-a-selection", E, "environment",
  '''    selected = (chosen or "").strip() or environ.get(TEST_ROOT_ENV, "").strip() \\
        or DEFAULT_TEST_ROOT''',
  '''    selected = chosen if chosen is not None else (
        environ.get(TEST_ROOT_ENV, "").strip() or DEFAULT_TEST_ROOT)''',
  ["TheBootstrapTestRootFollowsTheOperator.test_an_empty_or_blank_operand_is_not_a_selection"]),

 ("I1-the-recipe-assigns-its-own-root-again", J, "environment",
  '''	SELECTED="$(python3 -m tools.environment test-root --chosen "{{ROOT}}")"''',
  '''	SELECTED="{{ROOT}}"''',
  ["TheRecipesUseIt.test_the_recipe_asks_the_helper_for_the_root_rather_than_assigning_one"]),

 ("I1-an-unusable-selection-falls-through-again", S, "stack",
  '''        if place == named:
            raise AssertionError(''',
  '''        if False:
            raise AssertionError(''',
  ["TheChosenDiskRootIsNeverSilentlyReplaced.test_a_root_that_cannot_be_written_is_named_rather_than_passed_over",
   "TheChosenDiskRootIsNeverSilentlyReplaced.test_a_root_inside_the_checkout_is_named"]),

 ("I1-a-blank-selection-becomes-a-selection", S, "stack",
  '''    named = (os.environ.get(DISK_ROOT_VARIABLE) or "").strip()''',
  '''    named = os.environ.get(DISK_ROOT_VARIABLE)''',
  ["TheChosenDiskRootIsNeverSilentlyReplaced.test_an_unset_or_blank_selection_still_falls_back"]),
]


def restore():
    for place, content in PRISTINE.items():
        place.write_text(content)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(module, names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"]
        + ["tests.tools.test_%s.%s" % (module, one) for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, place, module, before, after, names in PROBES:
    restore()
    text = place.read_text()
    assert before in text, "probe %s does not apply" % label
    place.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(module, names)
    spent += seconds
    results.append({"probe": label, "file": place.name, "checks": names,
                    "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-52s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
one, seconds = run("environment", ["TheBootstrapTestRootFollowsTheOperator",
                                   "TheRecipesUseIt",
                                   "TheInterpreterOverrideIsExecutable"])
spent += seconds
other, seconds = run("stack", ["TheChosenDiskRootIsNeverSilentlyReplaced"])
spent += seconds
ok = one.returncode == 0 and other.returncode == 0
print("restored tree:", "OK" if ok else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": ok, "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
