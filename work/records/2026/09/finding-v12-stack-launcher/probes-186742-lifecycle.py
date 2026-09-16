"""W183883 claim186742 — reversal probes for the instance lifecycle.

The delivery slice this claim continued into: the lifecycle recipes take an
instance path and run the DEPLOYMENT'S OWN command, and the monitor is the
installed one. These ask whether each of those is held.

Every probe proves a PASSING BASELINE on pristine code first [J1]. A probe that
cannot pass before the reversal measures nothing.

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186742-lifecycle")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE,
                ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

FILES = {
    "justfile": TREE / "justfile",
    "instance": TREE / "python" / "tools" / "instance.py",
    "stack": TREE / "python" / "tools" / "stack.py",
    "stack_command": TREE / "python" / "tools" / "stack_command.py",
}
PRISTINE = {place: place.read_text() for place in FILES.values()}

ENVIRONMENT = "tests.tools.test_environment.TheInterpreterOverrideIsExecutable."
STACKS = "tests.tools.test_stack.TheInstalledMonitor."
INSTANCES = "tests.tools.test_instance.WhatARecipeAsksAnInstance."

PROBES = [
    {"label": "N1-the-recipes-run-this-checkout-instead-of-the-deployment",
     "file": "justfile",
     "before": '\t\tINSTALLED="$(python3 -m tools.instance command "{{INSTANCE}}")"\n\t\texec "$INSTALLED" start --instance "{{INSTANCE}}"',
     "after": '\t\ttrue',
     "checks": [ENVIRONMENT + "test_a_lifecycle_recipe_given_an_instance_runs_THAT_deployment"],
     "intended": "not found in"},
    {"label": "N2-the-monitor-recipe-rebuilds-the-snapshot-path-itself",
     "file": "justfile",
     "before": '\t\texec "$INSTALLED" monitor --instance "{{INSTANCE}}" --interval "{{INTERVAL}}"',
     "after": '\t\texec "$INSTALLED" view --status "{{INSTANCE}}/../state/status.json" --interval "{{INTERVAL}}"',
     "checks": [ENVIRONMENT + "test_the_monitor_takes_the_instance_and_the_interval"],
     "intended": "not found in"},
    {"label": "N3-a-verb-s-own-options-are-appended-after-the-verb-again",
     "file": "stack_command",
     "before": "        operands = list(operands)\n        head = []",
     "after": "        return stack.main(list(operands) + [subcommand])\n        head = []",
     "checks": [STACKS + "test_the_bundled_command_puts_a_verb_s_options_AFTER_the_verb",
                STACKS + "test_the_older_verbs_are_dispatched_exactly_as_before"],
     "intended": "AssertionError"},
    {"label": "N4-the-monitor-watches-a-snapshot-that-is-not-there",
     "file": "stack",
     "before": "    if not place.exists():",
     "after": "    if False:",
     "checks": [STACKS + "test_a_stack_that_has_published_nothing_is_said_so_rather_than_watched"],
     "intended": "StackRefusal not raised"},
    {"label": "N5-a-recipe-is-handed-a-path-out-of-a-selector-nothing-validated",
     "file": "instance",
     "before": "    try:\n        document = read(taken.instance)\n    except InstanceRefusal as refusal:",
     "after": "    try:\n        document = json.loads(Path(taken.instance).read_bytes())\n    except InstanceRefusal as refusal:",
     "checks": [INSTANCES + "test_a_selector_it_would_refuse_answers_nothing"],
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
(TREE.parent / "results-186742-lifecycle.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
