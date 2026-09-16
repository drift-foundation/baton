"""W183883 claim185653 reversal probes for `just setup`. Every probe must FAIL."""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
M = TREE / "python" / "tools" / "environment.py"
J = TREE / "justfile"
PRISTINE = {M: M.read_text(), J: J.read_text()}

PROBES = [
 ("setup-deletes-what-it-did-not-create", M,
  '''    if answer["state"] in ("foreign", "incompatible", "broken", "unusable"):''',
  '''    if False:''',
  ["PreparingIt.test_a_foreign_directory_is_refused_and_never_deleted",
   "PreparingIt.test_an_incompatible_environment_is_refused_and_never_deleted"]),

 ("a-directory-without-our-marker-is-ours", M,
  '''    if marker is None or marker.get("unreadable"):''',
  '''    if False:''',
  ["WhatItSeesThere.test_a_directory_this_setup_did_not_create_is_foreign",
   "WhatItSeesThere.test_an_unreadable_marker_is_foreign_rather_than_absent"]),

 ("a-marker-naming-another-path-still-counts", M,
  '''    if value.get("path") != str(Path(root).resolve()):''',
  '''    if False:''',
  ["WhatItSeesThere.test_a_marker_naming_another_path_is_foreign"]),

 ("the-declared-minimum-is-not-enforced", M,
  '''    if version[:2] < required_python():
        answer["state"] = "incompatible"''',
  '''    if False:
        answer["state"] = "incompatible"''',
  ["WhatItSeesThere.test_an_interpreter_below_the_declared_minimum_is_incompatible"]),

 ("a-too-old-interpreter-still-builds", M,
  '''    if version[:2] < required_python():
        raise SetupRefusal(
            str(chosen) + " is Python''',
  '''    if False:
        raise SetupRefusal(
            str(chosen) + " is Python''',
  ["PreparingIt.test_an_interpreter_below_the_minimum_builds_nothing"]),

 ("the-minimum-is-guessed-when-undeclared", M,
  '''    if not found:
        raise SetupRefusal(''',
  '''    if False:
        raise SetupRefusal(''',
  ["WhereItLives.test_a_pyproject_with_no_minimum_is_refused_rather_than_guessed"]),

 ("hashes-are-not-enforced", M,
  '''"--disable-pip-version-check", "--require-hashes",
                   "--ignore-installed", "-r", str(LOCK_PATH)],''',
  '''"--disable-pip-version-check",
                   "-r", str(LOCK_PATH)],''',
  ["PreparingIt.test_the_dependencies_are_installed_with_their_hashes_enforced"]),

 ("a-stale-lock-is-not-noticed", M,
  '''    if marker.get("lock_sha256") != answer["lock_sha256"]:''',
  '''    if False:''',
  ["WhatItSeesThere.test_an_environment_installed_from_another_lock_is_stale",
   "PreparingIt.test_a_stale_environment_is_reinstalled_and_not_recreated"]),

 ("a-repeated-setup-reinstalls-anyway", M,
  '''    if answer["state"] == "ready":
        print("already prepared: " + answer["path"], file=stream)''',
  '''    if False:
        print("already prepared: " + answer["path"], file=stream)''',
  ["PreparingIt.test_a_repeated_setup_installs_nothing_at_all"]),

 ("a-failed-install-hides-the-command", M,
  '''            + " install --no-cache-dir --disable-pip-version-check "
              "--require-hashes --ignore-installed -r " + str(LOCK_PATH)''',
  '''            + ""''',
  ["PreparingIt.test_a_refused_install_supplies_the_exact_command_and_deletes_nothing"]),

 ("the-refusal-goes-where-a-recipe-would-run-it", M,
  '''        print("refused: " + str(refusal), file=sys.stderr)''',
  '''        print("refused: " + str(refusal), file=stream)''',
  ["NamingTheInterpreter.test_the_refusal_never_reaches_the_stream_a_recipe_reads"]),

 ("a-recipe-falls-back-to-ambient-python", J,
  '''	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env PYTHONPATH=src:. "$PREPARED" -m tools.stack start''',
  '''	exec env PYTHONPATH=src:. python3 -m tools.stack start''',
  ["TheRecipesUseIt.test_every_stack_recipe_resolves_the_prepared_interpreter"]),

 ("starting-installs-as-a-side-effect", J,
  '''	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env PYTHONPATH=src:. "$PREPARED" -m tools.stack stop''',
  '''	python3 -m tools.environment setup
	PREPARED="$(python3 -m tools.environment interpreter)"
	exec env PYTHONPATH=src:. "$PREPARED" -m tools.stack stop''',
  ["TheRecipesUseIt.test_no_stack_recipe_installs_anything"]),
]


def restore():
    for place, content in PRISTINE.items():
        place.write_text(content)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(names):
    started = time.monotonic()
    done = subprocess.run([sys.executable, "-B", "-m", "unittest"]
                          + ["tests.tools.test_environment." + one for one in names],
                          cwd=str(TREE / "python"), capture_output=True,
                          text=True, timeout=600)
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, place, before, after, names in PROBES:
    restore()
    text = place.read_text()
    assert before in text, "probe %s does not apply" % label
    place.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(names)
    spent += seconds
    results.append({"probe": label, "file": place.name, "checks": names,
                    "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-46s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
done, seconds = run(["WhereItLives", "WhatItSeesThere", "NamingTheInterpreter",
                     "PreparingIt", "TheRecipesUseIt"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
